/** React hook wrapping the outbound-call controller + telephony readiness. */

import { useEffect, useMemo, useRef, useState } from "react";
import {
  getCallStatus,
  getTelephonyStatus,
  startOutboundCall,
} from "../api/calls";
import { createCallController } from "./callController";

export default function useTwilioCall({ sessionId, projectId, language } = {}) {
  const [readiness, setReadiness] = useState(null); // null=checking
  const [callState, setCallState] = useState({
    phase: "idle",
    call: null,
    error: null,
    phoneError: null,
  });

  const contextRef = useRef({ sessionId, projectId, language });
  contextRef.current = { sessionId, projectId, language };

  const controller = useMemo(
    () =>
      createCallController({
        startCall: startOutboundCall,
        fetchStatus: getCallStatus,
        onChange: setCallState,
      }),
    []
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await getTelephonyStatus();
        if (!cancelled) setReadiness(data);
      } catch {
        if (!cancelled) setReadiness({ enabled: false, ready: false, problems: [] });
      }
    })();
    return () => {
      cancelled = true;
      controller.dispose();
    };
  }, [controller]);

  return {
    readiness,
    ...callState,
    calling: callState.phase === "calling",
    dial: (rawPhone, extraContext = {}) =>
      controller.dial(rawPhone, { ...contextRef.current, ...extraContext }),
    dialLead: (leadId) => controller.dialLead(leadId),
  };
}
