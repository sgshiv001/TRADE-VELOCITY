import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { ActivityIndicator, Appearance, AppState, Platform, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View, useColorScheme } from "react-native";
import * as LocalAuthentication from "expo-local-authentication";
import * as SecureStore from "expo-secure-store";
import { SafeAreaView } from "react-native-safe-area-context";
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

const palettes = {
  dark: {background: "#0c1218", panel: "#141e27", raised: "#1b2833", line: "#2a3a47", text: "#f2f7f8", muted: "#a2b4c0", action: "#62e6bb", onAction: "#08271e", error: "#ff9ba5", hero: "#10362e", heroLine: "#24564a"},
  light: {background: "#f1f5f6", panel: "#ffffff", raised: "#eaf1f3", line: "#d5e0e4", text: "#13242c", muted: "#4c626d", action: "#09644d", onAction: "#ffffff", error: "#a2233b", hero: "#e1f3ee", heroLine: "#b4d9ce"},
};
function createTheme(colors: typeof palettes.dark) {
  const fontFamily = Platform.select({android: "sans-serif"});
  return StyleSheet.create({
    screen: {flex: 1, backgroundColor: colors.background},
    section: {width: "100%", maxWidth: 660, alignSelf: "center", padding: 16, paddingBottom: 28, gap: 16},
    panel: {backgroundColor: colors.panel, borderRadius: 16, padding: 14, gap: 10, borderWidth: 1, borderColor: colors.line},
    hero: {backgroundColor: colors.hero, borderColor: colors.heroLine, borderRadius: 20, padding: 17, gap: 10, borderWidth: 1},
    row: {flexDirection: "row", alignItems: "center", gap: 10},
    between: {flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 10},
    title: {fontFamily, color: colors.text, fontSize: 30, fontWeight: "700", letterSpacing: -0.65},
    sectionTitle: {fontFamily, color: colors.text, fontSize: 17, fontWeight: "700"},
    value: {fontFamily, color: colors.text, fontSize: 31, fontWeight: "700", fontVariant: ["tabular-nums"]},
    number: {fontFamily, color: colors.text, fontSize: 16, fontWeight: "700", fontVariant: ["tabular-nums"]},
    text: {fontFamily, color: colors.text, fontSize: 15},
    subtle: {fontFamily, color: colors.muted, fontSize: 13, lineHeight: 18},
    eyebrow: {fontFamily, color: colors.action, fontSize: 11, letterSpacing: 1.3, fontWeight: "700"},
    error: {fontFamily, color: colors.error, fontSize: 14, lineHeight: 19},
    field: {fontFamily, fontSize: 15, backgroundColor: colors.raised, borderWidth: 1, borderColor: colors.line, borderRadius: 12, color: colors.text, minHeight: 48, paddingHorizontal: 12},
    action: {backgroundColor: colors.action, borderRadius: 12, minHeight: 46, paddingHorizontal: 13, paddingVertical: 9, alignItems: "center", justifyContent: "center"},
    actionText: {fontFamily, color: colors.onAction, fontSize: 14, fontWeight: "700", textAlign: "center"},
    link: {fontFamily, color: colors.action, fontSize: 14, fontWeight: "700"},
  });
}
const themes = {light: createTheme(palettes.light), dark: createTheme(palettes.dark)};
type ThemeOption = keyof typeof themes | "system";
const themeKey = "tradevelocity-theme-v1";
const themeOptions = [
  {value: "system", label: "System"},
  {value: "light", label: "Light"},
  {value: "dark", label: "Dark"},
] as const;
const ThemeContext = createContext<{selection: ThemeOption; select(value: ThemeOption): void}>({
  selection: "system", select: () => {},
});

export function MobileAppearance({children}: {children: ReactNode}) {
  const [selection, select] = useState<ThemeOption | null>(null);
  useEffect(() => {
    let active = true;
    void SecureStore.getItemAsync(themeKey).then(saved => {
      if (!active) return;
      const value = themeOptions.find(option => option.value === saved)?.value ?? "system";
      select(current => current ?? value);
    }).catch(() => {});
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (selection === null) return;
    Appearance.setColorScheme(selection === "system" ? "auto" : selection);
    void SecureStore.setItemAsync(themeKey, selection).catch(() => {});
  }, [selection]);
  return <ThemeContext.Provider value={{selection: selection ?? "system", select}}>{children}</ThemeContext.Provider>;
}

export function useMobileTheme() {
  const {selection} = useContext(ThemeContext);
  const system = useColorScheme() === "light" ? "light" : "dark";
  const mode = selection === "system" ? system : selection;
  return {theme: themes[mode], colors: palettes[mode], mode};
}

export function MobileThemePicker() {
  const {selection, select} = useContext(ThemeContext);
  const {theme, colors} = useMobileTheme();
  return <View style={theme.panel}>
    <Text style={theme.text}>Theme</Text>
    <View accessibilityRole="radiogroup" style={{flexDirection: "row", flexWrap: "wrap", gap: 8}}>
      {themeOptions.map(({value, label}) => {
        const selected = value === selection;
        return <Pressable key={value} accessibilityRole="radio" accessibilityState={{checked: selected}}
          onPress={() => select(value)} style={[theme.action, !selected && {
            backgroundColor: colors.background, borderColor: colors.line, borderWidth: 1,
          }]}>
          <Text style={selected ? theme.actionText : theme.text}>{label}</Text>
        </Pressable>;
      })}
    </View>
  </View>;
}

export function Screen({title, children, subtitle, accessory, refresh, refreshing = false}: {
  title: string; children: ReactNode; subtitle?: string; accessory?: ReactNode; refresh?: () => void; refreshing?: boolean;
}) {
  const {theme, colors} = useMobileTheme();
  return <SafeAreaView style={theme.screen} edges={["top", "right", "left"]}>
    <ScrollView style={theme.screen} contentContainerStyle={theme.section} keyboardShouldPersistTaps="handled"
      refreshControl={refresh ? <RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.action} colors={[colors.action]} progressBackgroundColor={colors.panel} /> : undefined}>
      <View style={theme.between}>
        <View style={{flex: 1, gap: 3}}><Text style={theme.title} accessibilityRole="header">{title}</Text>
          {subtitle && <Text style={theme.subtle}>{subtitle}</Text>}</View>
        {accessory}
      </View>
      {children}
    </ScrollView>
  </SafeAreaView>;
}

export function Action({title, onPress, disabled = false, kind = "primary"}: {
  title: string; onPress(): void; disabled?: boolean; kind?: "primary" | "secondary" | "danger";
}) {
  const {theme, colors} = useMobileTheme();
  return <Pressable accessibilityRole="button" accessibilityState={{disabled}} disabled={disabled}
    style={({pressed}) => [theme.action, kind !== "primary" && {backgroundColor: colors.raised, borderColor: colors.line, borderWidth: 1},
      (disabled || pressed) && {opacity: disabled ? .48 : .78}]} onPress={onPress}>
    <Text style={[theme.actionText, kind !== "primary" && {color: kind === "danger" ? colors.error : colors.text}]}>{title}</Text>
  </Pressable>;
}

export function DataState({message, error, retry}: {message: string; error?: string; retry?: () => void}) {
  const {theme, colors} = useMobileTheme();
  return <View style={theme.panel} accessibilityLiveRegion="polite">
    <View style={theme.row}>
      {!error && <ActivityIndicator color={colors.action} />}
      <Text style={[error ? theme.error : theme.subtle, {flex: 1}]}>{error || message}</Text>
    </View>
    {error && retry && <Action title="Try again" kind="secondary" onPress={retry} />}
  </View>;
}

function reason(error: unknown) {
  return error instanceof Error ? error.message : "The request could not be completed.";
}

export function MobileSession({children}: {children: ReactNode}) {
  const {theme, colors} = useMobileTheme();
  const [session, setSession] = useState<Session | null>(null);
  const [locked, setLocked] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [verifySignup, setVerifySignup] = useState(false);
  const [verificationToken, setVerificationToken] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const generation = useRef(0);
  const enteringCodes = register && verifySignup && Boolean(verificationToken);

  function clearVerification() {
    setVerificationToken("");
    setEmailCode("");
  }

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

  async function toggleRegistration() {
    setError("");
    clearVerification();
    if (register) {
      setRegister(false);
      return;
    }
    setBusy(true);
    try {
      const status = await createClient(origin)<{signup_verification_required?: boolean}>("/auth/status");
      setVerifySignup(Boolean(status.signup_verification_required));
      setRegister(true);
    } catch (cause) { setError(reason(cause)); }
    finally { setBusy(false); }
  }

  async function requestEmailCode() {
    setBusy(true); setError("");
    try {
      const result = await createClient(origin)<{verification_token: string}>("/auth/signup/start", {
        method: "POST", body: JSON.stringify({username: username.trim(), email: email.trim()}),
      });
      setEmailCode("");
      setVerificationToken(result.verification_token);
    } catch (cause) { setError(reason(cause)); }
    finally { setBusy(false); }
  }

  async function submit() {
    if (register && password.length < 12) {
      setError("Use a password with at least 12 characters");
      return;
    }
    if (register && verifySignup && !verificationToken) return requestEmailCode();
    setBusy(true); setError("");
    try {
      const next = await createClient(origin)<{token: string}>(`/auth/device/${register ? "register" : "login"}`,
        {method: "POST", body: JSON.stringify({username: username.trim(), password, ...(enteringCodes ? {
          verification_token: verificationToken, email_code: emailCode,
        } : {})})});
      await SecureStore.setItemAsync(sessionKey, next.token);
      setPassword("");
      setEmail("");
      setRegister(false);
      clearVerification();
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

  const request: Request = useCallback(async (path, init) => {
    if (!session) throw new Error("Sign in to TradeVelocity");
    try {
      return await createClient(origin, {token: session.token, workspace: session.trader.workspace_id})(path, init);
    } catch (cause) {
      if (cause instanceof TradeVelocityApiError && cause.status === 401) {
        await SecureStore.deleteItemAsync(sessionKey);
        setSession(current => current === session ? null : current);
      }
      throw cause;
    }
  }, [session]);

  if (restoring) return <Screen title="TradeVelocity"><DataState message="Checking your session…" /></Screen>;
  if (session) {
    return <SessionContext.Provider value={{request, trader: session.trader, signOut, enableLock, revision}}>{children}</SessionContext.Provider>;
  }
  return <Screen title="TradeVelocity" subtitle="Your paper trading workspace">
    {error && <Text accessibilityRole="alert" style={theme.error}>{error}</Text>}
    {locked ? <Action title="Unlock your session" onPress={() => void unlock()} /> : <View style={theme.panel}>
      <Text style={theme.text}>{register ? "Create your account" : "Sign in to your paper trading account"}</Text>
      {enteringCodes ? <>
        <Text style={theme.subtle}>Enter the code sent to your email within 10 minutes.</Text>
        <TextInput accessibilityLabel="Email code" style={theme.field} keyboardType="number-pad" maxLength={6} autoComplete="one-time-code"
          placeholder="Email code" placeholderTextColor={colors.muted} value={emailCode} onChangeText={setEmailCode} />
      </> : <>
      <TextInput accessibilityLabel="Username" style={theme.field} autoCapitalize="none" autoCorrect={false} autoComplete="username"
        placeholder="Username" placeholderTextColor={colors.muted} value={username} onChangeText={setUsername} editable={!busy} />
      <TextInput accessibilityLabel="Password" style={theme.field} secureTextEntry autoComplete={register ? "new-password" : "current-password"}
        placeholder="Password" placeholderTextColor={colors.muted} value={password} onChangeText={setPassword} editable={!busy} />
      {register && verifySignup &&
        <TextInput accessibilityLabel="Email" style={theme.field} keyboardType="email-address" autoCapitalize="none" autoComplete="email"
          placeholder="Email" placeholderTextColor={colors.muted} value={email} onChangeText={setEmail} editable={!busy} />}
      </>}
      <Action title={register ? verifySignup && !enteringCodes ? "Send email code" : "Create account" : "Sign in"}
        disabled={busy || !username || !password || Boolean(register && verifySignup &&
          (enteringCodes ? emailCode.length !== 6 : !email))} onPress={() => void submit()} />
      {enteringCodes && <>
        <Pressable accessibilityRole="button" disabled={busy} onPress={() => void requestEmailCode()}>
          <Text style={theme.link}>Send a new code</Text>
        </Pressable>
        <Pressable accessibilityRole="button" disabled={busy} onPress={() => { clearVerification(); setError(""); }}>
          <Text style={theme.link}>Edit email</Text>
        </Pressable>
      </>}
      <Pressable accessibilityRole="button" disabled={busy} onPress={() => void toggleRegistration()}>
        <Text style={theme.link}>{register ? "Use existing account" : "Create an account"}</Text>
      </Pressable>
    </View>}
    <MobileThemePicker />
  </Screen>;
}
