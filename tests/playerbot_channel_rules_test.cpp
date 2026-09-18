// Unit tests for playerbot_channel_rules.h - the second channel's partition.
//
//   docker run --rm -v "$(pwd -W)":/w -w /w gcc:13 bash -c
//     "g++ -Wall -Wextra -o /tmp/t tests/playerbot_channel_rules_test.cpp && /tmp/t"
#include <cassert>
#include <cstdio>

#include "../linux-port/overlays/playerbot/src/game/src/playerbot_channel_rules.h"

using namespace playerbot_channel_rules;

int main()
{
	// Switched off, every bot lives on the first channel and nothing else
	// starts any: a world that never asked for a second channel is unchanged.
	for (unsigned int pid = 4; pid < 2504; ++pid)
		assert(ChannelOf(pid, false, 40, false) == 1);
	assert(ShareOfTotal(1500, false, 40, 1, 1000) == 1500);
	assert(ShareOfTotal(1500, false, 40, 2, 1000) == 0);

	// Switched on, the spread matches the share across the seed's whole range
	// - and inside each kingdom's run of pids, which is contiguous.
	{
		int second = 0;
		for (unsigned int pid = 4; pid < 2504; ++pid)
			second += ChannelOf(pid, true, 40, false) == 2 ? 1 : 0;
		assert(second > 2500 * 36 / 100 && second < 2500 * 44 / 100);
		int shinsoo = 0;
		for (unsigned int pid = 1504; pid < 2004; ++pid)
			shinsoo += ChannelOf(pid, true, 40, false) == 2 ? 1 : 0;
		assert(shinsoo > 500 * 33 / 100 && shinsoo < 500 * 47 / 100);
	}

	// The same pid gets the same answer every time - every core asks.
	for (unsigned int pid = 4; pid < 2504; ++pid)
		assert(ChannelOf(pid, true, 40, false) == ChannelOf(pid, true, 40, false));

	// A bot that has kept a shop lives on the first channel whatever the spread.
	for (unsigned int pid = 4; pid < 2504; ++pid)
		assert(ChannelOf(pid, true, 90, true) == 1);

	// The share is clamped: the first channel always keeps some bots, and a
	// share of nothing is not a second channel.
	assert(ClampShare(0) == CH2_SHARE_MIN);
	assert(ClampShare(100) == CH2_SHARE_MAX);
	assert(ClampShare(40) == 40);

	// The two channels add up to the operator's number.
	assert(ShareOfTotal(1500, true, 40, 1, 1000) == 900);
	assert(ShareOfTotal(1500, true, 40, 2, 1000) == 600);
	assert(ShareOfTotal(1501, true, 40, 1, 1000) + ShareOfTotal(1501, true, 40, 2, 1000) == 1501);
	// The second channel short of identities: it takes what it has and the
	// first channel takes the rest.
	assert(ShareOfTotal(1500, true, 40, 2, 250) == 250);
	assert(ShareOfTotal(1500, true, 40, 1, 250) == 1250);
	// No bots on a third channel, ever; nothing from nothing.
	assert(ShareOfTotal(1500, true, 40, 3, 1000) == 0);
	assert(ShareOfTotal(0, true, 40, 1, 1000) == 0);

	std::printf("playerbot_channel_rules_test: OK\n");
	return 0;
}
