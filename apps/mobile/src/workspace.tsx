import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { AppState, Button, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import * as LocalAuthentication from "expo-local-authentication";
import * as SecureStore from "expo-secure-store";
import { createClient, TradeVelocityApiError, type Trader } from "@tradevelocity/client";

const origin = process.env.EXPO_PUBLIC_API_URL ?? "https://gettradevelocity.onrender.com";
if (!/^https:\/\/[a-z\d.-]+(?::\d+)?\/?$/i.test(origin)) throw new Error("The mobile API must be an HTTPS origin");
const sessionKey = "tradevelocity-auth-v1";
const biometricKey = "tradevelocity-device-lock-v1";
type Session = {token: string; trader: Trader};
type Request = ReturnType<typeof createClient>;
const SessionContext = createContext<{request: Request; trader: Trader; signOut(): Promise<void>; enableLock(): Promise<void>; revision: number} | null>(null);
export function useWorkspace() {
  const session = useContext(SessionContext);
  if (!session) throw new Error("Sign in to TradeVelocity");
  return session;
}

export const theme = StyleSheet.create({
  screen: {flex: 1, backgroundColor: "#080c14"},
  section: {padding: 18, gap: 12},
  panel: {backgroundColor: "#111827", borderRadius: 14, padding: 14, gap: 8, borderWidth: 1, borderColor: "#28354b"},
  title: {color: "#f8fafc", fontSize: 27, fontWeight: "700"},
  text: {color: "#f8fafc", fontSize: 16},
  subtle: {color: "#bdc9db", fontSize: 14},
  error: {color: "#fda4af", fontSize: 14},
  field: {backgroundColor: "#111827", borderWidth: 1, borderColor: "#566580", borderRadius: 10, color: "#f8fafc", minHeight: 48, paddingHorizontal: 12},
  action: {backgroundColor: "#4338ca", borderRadius: 10, padding: 12, alignItems: "center"},
  actionText: {color: "#fff", fontSize: 16, fontWeight: "700"},
});

export function Screen({title, children}: {title: string; children: ReactNode}) {
  return <ScrollView style={theme.screen} contentContainerStyle={theme.section} keyboardShouldPersistTaps="handled">
    <Text style={theme.title} accessibilityRole="header">{title}</Text>{children}
  </ScrollView>;
}

export function Action({title, onPress, disabled = false}: {title: string; onPress(): void; disabled?: boolean}) {
  return <Pressable accessibilityRole="button" accessibilityState={{disabled}} disabled={disabled}
    style={[theme.action, disabled && {opacity: 0.6}]} onPress={onPress}><Text style={theme.actionText}>{title}</Text></Pressable>;
}

function reason(error: unknown) {
  return error instanceof Error ? error.message : "The request could not be completed.";
}

export function MobileSession({children}: {children: ReactNode}) {
  const [session, setSession] = useState<Session | null>(null);
  const [locked, setLocked] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const generation = useRef(0);

  async function resume(token: string) {
    const current = ++generation.current;
    const result = await createClient(origin, {token})<{trader: Trader | null}>("/auth/status");
    if (current !== generation.current) return;
    if (!result.trader) {
      await SecureStore.deleteItemAsync(sessionKey);
      return;
    }
    setSession({token, trader: result.trader});
  }

  async function restore() {
    setError("");
    const token = await SecureStore.getItemAsync(sessionKey);
    if (!token) return;
    if (await SecureStore.getItemAsync(biometricKey)) {
      setLocked(true);
      return;
    }
    await resume(token);
  }

  useEffect(() => { void restore().catch(cause => setError(reason(cause))).finally(() => setRestoring(false)); }, []);
  useEffect(() => {
    if (!session) return;
    const onResume = AppState.addEventListener("change", state => {
      if (state === "active") setRevision(value => value + 1);
    });
    let stopped = false;
    let waiting = 0;
    let connection: WebSocket | null = null;
    let delay = 1000;
    const connect = () => {
      // React Native's WebSocket constructor accepts request headers as its third parameter.
      const Socket = WebSocket as unknown as new (url: string, protocols: string[], options: {headers: Record<string, string>}) => WebSocket;
      connection = new Socket(`${origin.replace(/\/$/, "").replace(/^https:/, "wss:")}/api/live?session_id=${encodeURIComponent(session.trader.workspace_id)}`, [],
        {headers: {Authorization: `Bearer ${session.token}`}});
      connection.onopen = () => { delay = 1000; };
      connection.onmessage = event => {
        try {
          const code = JSON.parse(String(event.data)).type;
          if (["connected", "changed", "exchange_changed"].includes(code)) setRevision(value => value + 1);
        } catch { /* An invalid event should not replace the current state. */ }
      };
      connection.onclose = () => {
        if (stopped) return;
        waiting = Number(setTimeout(connect, delay));
        delay = Math.min(15000, delay * 2);
      };
    };
    connect();
    return () => { stopped = true; clearTimeout(waiting); connection?.close(); onResume.remove(); };
  }, [session]);

  async function submit() {
    setBusy(true); setError("");
    try {
      const next = await createClient(origin)<{token: string}>(`/auth/device/${register ? "register" : "login"}`,
        {method: "POST", body: JSON.stringify({username: username.trim(), password})});
      await SecureStore.setItemAsync(sessionKey, next.token);
      setPassword("");
      await resume(next.token);
    } catch (cause) { setError(reason(cause)); }
    finally { setBusy(false); }
  }

  async function unlock() {
    setError("");
    try {
      const result = await LocalAuthentication.authenticateAsync({promptMessage: "Unlock TradeVelocity"});
      if (!result.success) return;
      const token = await SecureStore.getItemAsync(sessionKey);
      if (token) await resume(token);
      setLocked(false);
    } catch (cause) { setError(reason(cause)); }
  }

  async function signOut() {
    if (!session) return;
    await createClient(origin, {token: session.token})("/auth/logout", {method: "POST"});
    generation.current++;
    await SecureStore.deleteItemAsync(sessionKey);
    await SecureStore.deleteItemAsync(biometricKey);
    setSession(null);
    setPassword("");
  }

  async function enableLock() {
    if (!await LocalAuthentication.hasHardwareAsync() || !await LocalAuthentication.isEnrolledAsync()) {
      throw new Error("Enroll a biometric on this device first");
    }
    const result = await LocalAuthentication.authenticateAsync({promptMessage: "Enable the device lock"});
    if (result.success) await SecureStore.setItemAsync(biometricKey, "1");
  }

  if (restoring) return <Screen title="TradeVelocity"><Text style={theme.subtle}>Checking your session…</Text></Screen>;
  if (session) {
    const request: Request = async (path, init) => {
      try {
        return await createClient(origin, {token: session.token, workspace: session.trader.workspace_id})(path, init);
      } catch (cause) {
        if (cause instanceof TradeVelocityApiError && cause.status === 401) {
          await SecureStore.deleteItemAsync(sessionKey);
          setSession(null);
        }
        throw cause;
      }
    };
    return <SessionContext.Provider value={{request, trader: session.trader, signOut, enableLock, revision}}>{children}</SessionContext.Provider>;
  }
  return <Screen title="TradeVelocity">
    {error && <Text accessibilityRole="alert" style={theme.error}>{error}</Text>}
    {locked ? <Action title="Unlock your session" onPress={() => void unlock()} /> : <View style={theme.panel}>
      <Text style={theme.text}>{register ? "Create your account" : "Sign in to your paper trading account"}</Text>
      <TextInput accessibilityLabel="Username" style={theme.field} autoCapitalize="none" autoCorrect={false} autoComplete="username"
        placeholder="Username" placeholderTextColor="#94a3b8" value={username} onChangeText={setUsername} />
      <TextInput accessibilityLabel="Password" style={theme.field} secureTextEntry autoComplete={register ? "new-password" : "current-password"}
        placeholder="Password" placeholderTextColor="#94a3b8" value={password} onChangeText={setPassword} />
      <Action title={register ? "Create account" : "Sign in"} disabled={busy || !username || !password} onPress={() => void submit()} />
      <Button title={register ? "Use existing account" : "Create an account"} onPress={() => setRegister(!register)} />
    </View>}
  </Screen>;
}
