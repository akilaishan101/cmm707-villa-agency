(() => {
  const localHostnames = new Set(["localhost", "127.0.0.1"]);
  const defaultAnalyticsUrl = localHostnames.has(window.location.hostname)
    ? "http://localhost:8004/events"
    : "/analytics/events";
  const analyticsUrl =
    window.VILLA_ANALYTICS_URL || defaultAnalyticsUrl;
  const sessionKey = "villa_analytics_session_id";

  function createSessionId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }

    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function getSessionId() {
    let sessionId = sessionStorage.getItem(sessionKey);

    if (!sessionId) {
      sessionId = createSessionId();
      sessionStorage.setItem(sessionKey, sessionId);
    }

    return sessionId;
  }

  function getPropertyId() {
    const parameters = new URLSearchParams(window.location.search);
    const propertyId = Number(parameters.get("property_id"));

    if (propertyId > 0) {
      return propertyId;
    }

    return window.location.pathname.includes("property-details.html")
      ? 1
      : null;
  }

  function trackEvent(eventType, metadata = {}) {
    const payload = {
      event_type: eventType,
      page: window.location.pathname,
      property_id: getPropertyId(),
      session_id: getSessionId(),
      occurred_at: new Date().toISOString(),
      metadata,
    };

    fetch(analyticsUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {
      console.warn("Analytics event could not be sent");
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    trackEvent("page_view", {
      title: document.title,
    });

    if (window.location.pathname.includes("property-details.html")) {
      trackEvent("property_view", {
        title: document.title,
      });
    }
  });

  document.addEventListener("click", (event) => {
    const clickableElement = event.target.closest("a, button");

    if (
      clickableElement &&
      clickableElement.textContent
        .trim()
        .toLowerCase()
        .includes("schedule a visit")
    ) {
      trackEvent("schedule_visit_click", {
        label: clickableElement.textContent.trim(),
      });
    }
  });
})();
