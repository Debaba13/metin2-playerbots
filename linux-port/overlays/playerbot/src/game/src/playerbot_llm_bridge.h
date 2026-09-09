#ifndef __INC_METIN2_PLAYERBOT_LLM_BRIDGE_H__
#define __INC_METIN2_PLAYERBOT_LLM_BRIDGE_H__

// Asynchronous Cognitive LLM Bridge for Metin2 PlayerBots.
// Connects the deterministic PlayerBots C++ engine to the external mmo-llm-adapter.
// Operates on a dedicated background worker thread so game ticks never block on LLM inference.

#include <thread>
#include <mutex>
#include <condition_variable>
#include <deque>
#include <string>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>

namespace
{
	struct TPlayerBotLLMRequest
	{
		DWORD dwBotPID;
		char szBotName[CHARACTER_NAME_MAX_LEN + 1];
		BYTE bJob;
		BYTE bLevel;
		BYTE bPersonality;
		long lMapIndex;
		char szPlayerName[CHARACTER_NAME_MAX_LEN + 1];
		char szMessage[CHAT_MAX_LEN + 1];
		char szEventType[32]; // "whisper", "say"
	};

	struct TPlayerBotLLMResponse
	{
		DWORD dwBotPID;
		char szBotName[CHARACTER_NAME_MAX_LEN + 1];
		char szPlayerName[CHARACTER_NAME_MAX_LEN + 1];
		char szSpeechReply[CHAT_MAX_LEN + 1];
		char szPrimaryAction[64];
		char szFollowTarget[CHARACTER_NAME_MAX_LEN + 1];
		bool bSuccess;
	};

	static std::mutex s_llmMutex;
	static std::condition_variable s_llmCV;
	static std::deque<TPlayerBotLLMRequest> s_llmRequestQueue;
	static std::deque<TPlayerBotLLMResponse> s_llmResponseQueue;
	static std::thread* s_pLLMWorkerThread = NULL;
	static bool s_bLLMWorkerStop = false;
	static bool s_bLLMBridgeInitialized = false;

	// Escape special characters for valid JSON
	static std::string EscapeJSON(const char* s)
	{
		if (!s)
			return "";
		std::string res;
		for (; *s; ++s)
		{
			if (*s == '"') res += "\\\"";
			else if (*s == '\\') res += "\\\\";
			else if (*s == '\b') res += "\\b";
			else if (*s == '\f') res += "\\f";
			else if (*s == '\n') res += "\\n";
			else if (*s == '\r') res += "\\r";
			else if (*s == '\t') res += "\\t";
			else if ((unsigned char)*s >= 32 && (unsigned char)*s <= 126) res += *s;
			else res += ' ';
		}
		return res;
	}

	// Simple key-value JSON string extractor
	static bool ExtractJSONString(const std::string& json, const std::string& key, char* out, size_t outSize)
	{
		if (!out || outSize == 0)
			return false;
		out[0] = '\0';
		std::string search = "\"" + key + "\":";
		size_t pos = json.find(search);
		if (pos == std::string::npos)
			return false;
		pos += search.length();
		while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t' || json[pos] == '\r' || json[pos] == '\n'))
			pos++;
		if (pos >= json.length() || json[pos] != '"')
			return false;
		pos++; // Skip opening quote
		size_t outIdx = 0;
		while (pos < json.length() && json[pos] != '"' && outIdx + 1 < outSize)
		{
			if (json[pos] == '\\' && pos + 1 < json.length())
			{
				pos++;
				if (json[pos] == 'n') out[outIdx++] = ' ';
				else out[outIdx++] = json[pos];
			}
			else
			{
				out[outIdx++] = json[pos];
			}
			pos++;
		}
		out[outIdx] = '\0';
		return true;
	}

	// Background worker thread connecting to mmo-llm-adapter via HTTP POST
	static void PlayerBotLLMWorkerFunc()
	{
		const char* hostEnv = getenv("M2_LLM_ADAPTER_HOST");
		const char* portEnv = getenv("M2_LLM_ADAPTER_PORT");
		const char* host = (hostEnv && *hostEnv) ? hostEnv : "host.docker.internal";
		int port = (portEnv && *portEnv) ? atoi(portEnv) : 8080;

		while (!s_bLLMWorkerStop)
		{
			TPlayerBotLLMRequest req;
			{
				std::unique_lock<std::mutex> lock(s_llmMutex);
				s_llmCV.wait(lock, []() {
					return s_bLLMWorkerStop || !s_llmRequestQueue.empty();
				});
				if (s_bLLMWorkerStop)
					break;
				req = s_llmRequestQueue.front();
				s_llmRequestQueue.pop_front();
			}

			// Format JSON request body
			char jsonBody[1024];
			snprintf(jsonBody, sizeof(jsonBody),
				"{\"event_type\":\"%s\",\"bot_pid\":%u,\"player_name\":\"%s\","
				"\"message\":\"%s\",\"bot_profile\":{\"name\":\"%s\",\"level\":%u,\"map_index\":%ld,\"personality_id\":%u}}",
				EscapeJSON(req.szEventType).c_str(),
				req.dwBotPID,
				EscapeJSON(req.szPlayerName).c_str(),
				EscapeJSON(req.szMessage).c_str(),
				EscapeJSON(req.szBotName).c_str(),
				(unsigned int)req.bLevel,
				req.lMapIndex,
				(unsigned int)req.bPersonality
			);

			TPlayerBotLLMResponse resp;
			memset(&resp, 0, sizeof(resp));
			resp.dwBotPID = req.dwBotPID;
			strlcpy(resp.szBotName, req.szBotName, sizeof(resp.szBotName));
			strlcpy(resp.szPlayerName, req.szPlayerName, sizeof(resp.szPlayerName));
			resp.bSuccess = false;

			struct addrinfo hints, *res = NULL;
			memset(&hints, 0, sizeof(hints));
			hints.ai_family = AF_UNSPEC;
			hints.ai_socktype = SOCK_STREAM;
			char portStr[16];
			snprintf(portStr, sizeof(portStr), "%d", port);

			if (getaddrinfo(host, portStr, &hints, &res) == 0 && res)
			{
				int sock = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
				if (sock >= 0)
				{
					// Set non-blocking for connect timeout
					int flags = fcntl(sock, F_GETFL, 0);
					fcntl(sock, F_SETFL, flags | O_NONBLOCK);

					connect(sock, res->ai_addr, res->ai_addrlen);

					struct pollfd pfd;
					pfd.fd = sock;
					pfd.events = POLLOUT;
					// 1500ms timeout on connect
					if (poll(&pfd, 1, 1500) > 0 && (pfd.revents & POLLOUT))
					{
						char httpReq[2048];
						int reqLen = snprintf(httpReq, sizeof(httpReq),
							"POST /v1/metin2/event HTTP/1.1\r\n"
							"Host: %s:%d\r\n"
							"Content-Type: application/json\r\n"
							"Content-Length: %zu\r\n"
							"Connection: close\r\n\r\n"
							"%s",
							host, port, strlen(jsonBody), jsonBody
						);

						send(sock, httpReq, reqLen, 0);

						// Read response with 4000ms timeout
						pfd.events = POLLIN;
						std::string httpRes;
						while (poll(&pfd, 1, 4000) > 0 && (pfd.revents & POLLIN))
						{
							char buf[512];
							int r = recv(sock, buf, sizeof(buf) - 1, 0);
							if (r <= 0) break;
							buf[r] = '\0';
							httpRes += buf;
						}

						// Extract JSON body
						size_t bodyPos = httpRes.find("\r\n\r\n");
						if (bodyPos != std::string::npos)
						{
							std::string body = httpRes.substr(bodyPos + 4);
							ExtractJSONString(body, "speech_reply", resp.szSpeechReply, sizeof(resp.szSpeechReply));
							ExtractJSONString(body, "primary_action", resp.szPrimaryAction, sizeof(resp.szPrimaryAction));
							resp.bSuccess = (resp.szSpeechReply[0] != '\0' || resp.szPrimaryAction[0] != '\0');
						}
					}
					close(sock);
				}
				freeaddrinfo(res);
			}

			// Push response
			{
				std::lock_guard<std::mutex> lock(s_llmMutex);
				s_llmResponseQueue.push_back(resp);
			}
		}
	}

	// Starts worker thread once
	static void InitializePlayerBotLLMBridge()
	{
		if (s_bLLMBridgeInitialized)
			return;
		s_bLLMBridgeInitialized = true;
		s_pLLMWorkerThread = new std::thread(PlayerBotLLMWorkerFunc);
	}

	// Non-blocking dispatch called when a player whispers to a bot
	static bool DispatchPlayerBotLLMWhisper(LPCHARACTER player, LPCHARACTER bot, const char* text)
	{
		if (!player || !bot || !text || !*text)
			return false;
		InitializePlayerBotLLMBridge();

		TPlayerBotLLMRequest req;
		memset(&req, 0, sizeof(req));
		req.dwBotPID = bot->GetPlayerID();
		strlcpy(req.szBotName, bot->GetName(), sizeof(req.szBotName));
		req.bJob = bot->GetJob();
		req.bLevel = bot->GetLevel();
		req.bPersonality = GetPlayerBotPersonalityByPID(req.dwBotPID);
		req.lMapIndex = bot->GetMapIndex();
		strlcpy(req.szPlayerName, player->GetName(), sizeof(req.szPlayerName));
		strlcpy(req.szMessage, text, sizeof(req.szMessage));
		strlcpy(req.szEventType, "whisper", sizeof(req.szEventType));

		{
			std::lock_guard<std::mutex> lock(s_llmMutex);
			s_llmRequestQueue.push_back(req);
		}
		s_llmCV.notify_one();
		return true;
	}

	// Called on CPlayerBotManager::Update to consume completed LLM responses
	static void UpdatePlayerBotLLMBridge(DWORD dwNow)
	{
		std::deque<TPlayerBotLLMResponse> readyResponses;
		{
			std::lock_guard<std::mutex> lock(s_llmMutex);
			if (s_llmResponseQueue.empty())
				return;
			readyResponses.swap(s_llmResponseQueue);
		}

		while (!readyResponses.empty())
		{
			TPlayerBotLLMResponse res = readyResponses.front();
			readyResponses.pop_front();

			LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(res.dwBotPID);
			LPCHARACTER player = CHARACTER_MANAGER::instance().FindPC(res.szPlayerName);

			if (bot && player)
			{
				if (res.bSuccess && res.szSpeechReply[0] != '\0')
				{
					SendPlayerBotWhisper(bot, player, res.szSpeechReply);
				}
				else if (!res.bSuccess)
				{
					// Safe fallback when adapter is unreachable
					char reply[CHAT_MAX_LEN + 1];
					FormatPlayerBotText(reply, sizeof(reply), "",
						"Nie handluje teraz, poluje. Zajrzyj na stragany w Joan i Bokjung");
					SendPlayerBotWhisper(bot, player, reply);
				}
			}
		}
	}
}

#endif
