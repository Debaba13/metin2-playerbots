#ifndef PLAYERBOT_OFFLINE_POLICY_H
#define PLAYERBOT_OFFLINE_POLICY_H
#include <cstdint>
#include <map>

// Process-local request journal; no character/item pointers. Only the AI arms
// requests. Native DB handlers mark transmission and completion. Never retry a
// transmitted request on timeout: native Ikarus has no idempotency key.
namespace playerbot_offline {
enum Op { None, Create, Add, Edit, Remove, WithdrawItem, Buy };
struct Request {
    Op op = None;
    uint32_t item = 0, started = 0;
    bool sent = false, done = false, success = false, warned = false;
    uint32_t vnum = 0, count = 0, unitPrice = 0, skill = 0;
    uint8_t refine = 0;
};
inline std::map<uint32_t, Request> requests;
inline bool Due(uint32_t now, uint32_t at) {
    return at == 0 || int32_t(now - at) >= 0;
}
inline bool Begin(uint32_t pid, Op op, uint32_t item, uint32_t now) {
    if (requests.count(pid)) return false;
    requests.emplace(pid, Request{op, item, now});
    return true;
}
inline void Sent(uint32_t pid, Op op, uint32_t item) {
    auto it = requests.find(pid);
    if (it != requests.end() && it->second.op == op && it->second.item == item)
        it->second.sent = true;
}
inline void Complete(uint32_t pid, Op op, uint32_t item, bool ok = true) {
    auto it = requests.find(pid);
    if (it != requests.end() && it->second.sent && it->second.op == op && it->second.item == item) {
        it->second.done = true;
        it->second.success = ok;
    }
}
inline bool EndCall(uint32_t pid) {
    auto it = requests.find(pid);
    if (it == requests.end()) return false;
    if (it->second.sent) return true;
    requests.erase(it); // synchronous refusal, no DB mutation submitted
    return false;
}
struct State {
    uint32_t nextService = 0, visitUntil = 0, nextStep = 0;
    uint32_t nextReprice = 0, repriceItem = 0;
    uint32_t nextBrowse = 0, buyOwner = 0, buyItem = 0, buyUntil = 0;
    uint32_t observedShop = 0;
    bool visiting = false;
};
inline bool Fits(int cell, int height, int width, int cells) {
    return width > 0 && height > 0 && cell >= 0 && cell < cells &&
        height <= cells / width && cell + (height - 1) * width < cells;
}
inline int64_t Affordable(int64_t wallet, int64_t reserve, int64_t floor) {
    return wallet > reserve + floor ? wallet - reserve - floor : 0;
}
}
#endif
