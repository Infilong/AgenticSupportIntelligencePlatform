import { test as base } from "@playwright/test";

// Keep only transport metadata. Never attach URLs, headers, bodies or user content.
export const test = base.extend<{ agentNetworkDiagnostics: void }>({
  agentNetworkDiagnostics: [async ({ page }, use, testInfo) => {
    const session = await page.context().newCDPSession(page);
    const tracked = new Map<string, string>();
    const events: Record<string, unknown>[] = [];
    const record = (requestId: string, phase: string, fields = {}) => {
      const endpoint = tracked.get(requestId);
      if (endpoint) events.push({ requestId, endpoint, phase, time: Date.now(), ...fields });
    };
    session.on("Network.requestWillBeSent", ({ requestId, request }) => {
      const path = new URL(request.url).pathname;
      const endpoint = path === "/" ? "navigation"
        : /\/agents\/[^/]+\/summary$/.test(path) ? "agent-summary"
        : /\/agents\/[^/]+\/workflow$/.test(path) ? "agent-workflow"
        : /\/agents$/.test(path) ? "agent-list" : null;
      if (endpoint) {
        tracked.set(requestId, endpoint);
        record(requestId, "request");
      }
    });
    session.on("Network.responseReceived", ({ requestId, response }) => {
      const timing = response.timing;
      record(requestId, "response", { status: response.status, timing: timing ? {
        proxyStart: timing.proxyStart, proxyEnd: timing.proxyEnd,
        dnsStart: timing.dnsStart, dnsEnd: timing.dnsEnd,
        connectStart: timing.connectStart, connectEnd: timing.connectEnd,
        sslStart: timing.sslStart, sslEnd: timing.sslEnd,
        sendStart: timing.sendStart, receiveHeadersEnd: timing.receiveHeadersEnd,
      } : null });
    });
    session.on("Network.loadingFinished", ({ requestId }) => record(requestId, "finished"));
    session.on("Network.loadingFailed", ({ requestId, canceled, blockedReason }) => {
      record(requestId, "failed", { canceled, blockedReason });
    });
    await session.send("Network.enable");
    const profile = process.env.BROWSER_CPU_PROFILE === "1";
    if (profile) {
      await session.send("Profiler.enable");
      await session.send("Profiler.setSamplingInterval", { interval: 10000 });
      await session.send("Profiler.start");
    }
    await use();
    if (profile) {
      const { profile: cpu } = await session.send("Profiler.stop");
      // Keep sample IDs/timing and function names, never script URLs or source text.
      await testInfo.attach("browser-cpu", {
        body: JSON.stringify({
          startTime: cpu.startTime, endTime: cpu.endTime,
          samples: cpu.samples, timeDeltas: cpu.timeDeltas,
          nodes: cpu.nodes.map((node) => ({
            id: node.id, children: node.children, hitCount: node.hitCount,
            functionName: node.callFrame.functionName,
          })),
        }), contentType: "application/json",
      });
    }
    await testInfo.attach("agent-network", {
      body: JSON.stringify(events, null, 2), contentType: "application/json",
    });
    await session.detach();
  }, { auto: true }],
});
