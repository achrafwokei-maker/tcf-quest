// Online accounts (beta only). Firebase does the sign-in in the browser (Google or email/password);
// the server checks the resulting ID token once and keeps its own signed cookie. The Firebase web
// config comes from the server at runtime: it identifies the project and is public, not a secret.
// The SDK is loaded only when accounts are switched on, so the local app never downloads it.

export interface FirebaseConfig { apiKey: string; authDomain: string; projectId: string }
export interface Me { beta: boolean; tester: string | null; firebase: FirebaseConfig | null }

let ready: Promise<typeof import("firebase/auth") & { auth: import("firebase/auth").Auth }> | null = null;

function load(config: FirebaseConfig) {
  ready ??= (async () => {
    const [{ initializeApp }, fa] = await Promise.all([import("firebase/app"), import("firebase/auth")]);
    const auth = fa.getAuth(initializeApp(config));
    auth.languageCode = "fr";
    return { ...fa, auth };
  })();
  return ready;
}

/** Hands Firebase's ID token to the server; returns the account, or throws with a readable message. */
async function exchange(idToken: string): Promise<Me> {
  const r = await fetch("/api/auth/firebase", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id_token: idToken }) });
  const body = await r.json().catch(() => ({}));
  if (r.ok) return { beta: true, tester: body.tester, firebase: null };
  if (body.detail === "verify_email") throw new NeedsVerification();
  if (body.detail === "accounts_full") throw new Error("The beta is full for now. Ask the owner for a place.");
  throw new Error(body.detail ?? "Sign-in failed. Please try again.");
}

export class NeedsVerification extends Error {
  constructor() { super("Check your inbox: click the link we sent you, then press “I've confirmed my email”."); }
}

const friendly = (e: unknown): Error => {
  const code = (e as { code?: string })?.code ?? "";
  const map: Record<string, string> = {
    "auth/invalid-credential": "Wrong email or password.",
    "auth/wrong-password": "Wrong email or password.",
    "auth/user-not-found": "Wrong email or password.",
    "auth/email-already-in-use": "This email already has an account: sign in instead.",
    "auth/weak-password": "Choose a longer password (at least 8 characters).",
    "auth/invalid-email": "That email address doesn't look right.",
    "auth/too-many-requests": "Too many attempts. Wait a few minutes and try again.",
    "auth/popup-closed-by-user": "The Google window was closed before signing in.",
    "auth/network-request-failed": "No connection. Check your internet and try again.",
  };
  return e instanceof NeedsVerification || !code ? (e as Error) : new Error(map[code] ?? "Sign-in failed. Please try again.");
};

export async function signInWithGoogle(config: FirebaseConfig): Promise<Me> {
  const f = await load(config);
  try {
    const cred = await f.signInWithPopup(f.auth, new f.GoogleAuthProvider());
    return await exchange(await cred.user.getIdToken());
  } catch (e) { throw friendly(e); }
}

export async function signInWithEmail(config: FirebaseConfig, email: string, password: string, create: boolean): Promise<Me> {
  const f = await load(config);
  try {
    const cred = create
      ? await f.createUserWithEmailAndPassword(f.auth, email.trim(), password)
      : await f.signInWithEmailAndPassword(f.auth, email.trim(), password);
    if (!cred.user.emailVerified) {
      await f.sendEmailVerification(cred.user);
      throw new NeedsVerification();
    }
    return await exchange(await cred.user.getIdToken());
  } catch (e) { throw friendly(e); }
}

/** After the learner clicks the link in the email: refresh the token so it says "verified". */
export async function confirmVerified(config: FirebaseConfig): Promise<Me> {
  const f = await load(config);
  const user = f.auth.currentUser;
  if (!user) throw new Error("Please sign in again.");
  await user.reload();
  if (!user.emailVerified) throw new NeedsVerification();
  return exchange(await user.getIdToken(true));
}

export async function resetPassword(config: FirebaseConfig, email: string): Promise<void> {
  const f = await load(config);
  try { await f.sendPasswordResetEmail(f.auth, email.trim()); } catch (e) { throw friendly(e); }
}

export async function signOut(config: FirebaseConfig | null): Promise<void> {
  await fetch("/api/beta/logout", { method: "POST" });
  if (config) await (await load(config)).signOut((await load(config)).auth).catch(() => undefined);
  window.location.assign("/");
}
