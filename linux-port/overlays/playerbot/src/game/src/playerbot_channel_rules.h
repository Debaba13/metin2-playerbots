#ifndef __INC_PLAYERBOT_CHANNEL_RULES_H__
#define __INC_PLAYERBOT_CHANNEL_RULES_H__

// The second channel as pure policy: which channel a registered bot lives on,
// and how much of the operator's number each channel starts. No engine types,
// unit-tested (tests/playerbot_channel_rules_test.cpp).
//
// A bot must live on exactly one channel. Every core loads the registry for
// itself and nothing tells one channel what another decided, so the answer has
// to come out the same on every core from the same inputs: the pid, the switch
// and the share from the container's environment, and whether the bot is
// pinned. Two cores that disagreed about one pid would both log it in - the
// db core serves a bot's load to anyone who asks, P2P_MANAGER overwrites its
// entry without a word, and the two copies' saves would duplicate every item
// either of them sold ("a same pid on two cores", read in the engine on 18
// September before any of this was written).
//
// A pinned bot is one that has kept an offline shop. Shops are the first
// channel's alone (the operator's rule: "wszystkie sklepy tylko na ch1"), a
// shop's entity stands on the channel it was opened on, and a keeper on the
// other channel could never serve its counter or take its yang out again - so
// every bot that has ever owned a shop lives on the first channel for good.
// The pins only grow (player.playerbot_channel_pin), which is what keeps the
// answer the same on a core restarted in the middle of a session: nobody on
// the second channel can open a shop, so no second-channel bot can become
// pinned while the other channel's cores are running.
//
// Only the first two channels carry bots. A third or fourth is players'.
namespace playerbot_channel_rules
{
	// The share of the population on the second channel, clamped: the first
	// channel is where the shops are, so it always keeps some.
	const int CH2_SHARE_MIN = 10;
	const int CH2_SHARE_MAX = 90;
	const int CH2_SHARE_DEFAULT = 40;

	inline int ClampShare(int percent)
	{
		if (percent < CH2_SHARE_MIN)
			return CH2_SHARE_MIN;
		if (percent > CH2_SHARE_MAX)
			return CH2_SHARE_MAX;
		return percent;
	}

	// A stable spread of pids over 0..99. Consecutive pids - the seed creates
	// them in runs by kingdom - must not land in blocks, so the pid is mixed
	// (the finaliser of MurmurHash3) before it is reduced.
	inline unsigned int SpreadPercent(unsigned int pid)
	{
		unsigned int h = pid ^ 0x43483232u;
		h ^= h >> 16;
		h *= 0x85ebca6bu;
		h ^= h >> 13;
		h *= 0xc2b2ae35u;
		h ^= h >> 16;
		return h % 100u;
	}

	// The channel a registered bot lives on.
	inline int ChannelOf(unsigned int pid, bool ch2Enabled, int sharePercent, bool pinned)
	{
		if (!ch2Enabled || pinned)
			return 1;
		return SpreadPercent(pid) < (unsigned int)ClampShare(sharePercent) ? 2 : 1;
	}

	// How many of the operator's number `channel` starts. The second channel
	// takes its share, never more than the identities it has; the first takes
	// the rest, so the two add up to the number whenever the identities allow.
	// With the switch off the first channel takes all of it and no other
	// channel takes anything - which is also what a third channel always gets.
	inline int ShareOfTotal(int total, bool ch2Enabled, int sharePercent, int channel,
			int secondChannelIdentities)
	{
		if (total <= 0 || channel < 1 || channel > 2)
			return 0;
		if (!ch2Enabled)
			return channel == 1 ? total : 0;
		int second = total * ClampShare(sharePercent) / 100;
		if (secondChannelIdentities >= 0 && second > secondChannelIdentities)
			second = secondChannelIdentities;
		return channel == 2 ? second : total - second;
	}
}

#endif
