---
name: firebase
description: "Integrates Firebase services (Authentication, Firestore, Realtime Database, Storage, Cloud Functions, FCM, Analytics, Remote Config, App Check) into web and Node.js applications. Use when asked to: set up Firebase in a web or Node.js app, implement user authentication with Firebase, read or write data to Firestore or Realtime Database, upload files to Firebase Storage, send push notifications with Firebase Cloud Messaging, call Cloud Functions from a client, configure Firebase Remote Config, or protect a backend with Firebase App Check."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [firebase, firestore, authentication, realtime-database, cloud-functions, storage, fcm, analytics]
---

# Firebase Skill

## Quick Start

```bash
npm install firebase
```

```js
// firebase.js — initialize once, import everywhere
import { initializeApp } from 'firebase/app';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export default app;
```

## When to Use

Use this skill when asked to:
- Set up or configure Firebase in a web or Node.js project
- Implement sign-in, sign-up, or OAuth authentication (Google, GitHub, email/password)
- Read, write, update, or delete documents in Firestore or Realtime Database
- Listen to real-time data changes with Firestore or Realtime Database subscriptions
- Upload, download, or manage files in Firebase Storage
- Send push notifications using Firebase Cloud Messaging (FCM)
- Call or deploy Cloud Functions from a client application
- Configure feature flags or A/B tests with Firebase Remote Config
- Track user events with Google Analytics for Firebase
- Protect backend resources using Firebase App Check

## Core Patterns

### Pattern 1: Authentication — Email/Password + Google OAuth (Source: official)

Handles the two most common auth flows. Always use `onAuthStateChanged` as the
single source of truth for auth state rather than reading `currentUser` directly.

```js
import { getAuth, createUserWithEmailAndPassword,
         signInWithPopup, GoogleAuthProvider,
         onAuthStateChanged, signOut } from 'firebase/auth';
import app from './firebase';

const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Email / password sign-up
export async function signUpWithEmail(email, password) {
  const credential = await createUserWithEmailAndPassword(auth, email, password);
  return credential.user;
}

// Google OAuth pop-up
export async function signInWithGoogle() {
  const result = await signInWithPopup(auth, googleProvider);
  return result.user;
}

// Reactive auth state — use this in your top-level component
export function onUserChanged(callback) {
  return onAuthStateChanged(auth, callback); // returns unsubscribe fn
}

export const logout = () => signOut(auth);
```

### Pattern 2: Cloud Firestore — CRUD + Real-time Listener (Source: official)

```js
import {
  getFirestore, collection, doc,
  addDoc, setDoc, getDoc, getDocs,
  updateDoc, deleteDoc,
  onSnapshot, query, where, orderBy, limit,
  serverTimestamp,
} from 'firebase/firestore';
import app from './firebase';

const db = getFirestore(app);

// CREATE — auto-generated ID
export async function createCity(data) {
  const ref = await addDoc(collection(db, 'cities'), {
    ...data,
    createdAt: serverTimestamp(),
  });
  return ref.id;
}

// READ — single document
export async function getCity(id) {
  const snap = await getDoc(doc(db, 'cities', id));
  return snap.exists() ? { id: snap.id, ...snap.data() } : null;
}

// READ — collection with filtering
export async function getLargeCities() {
  const q = query(
    collection(db, 'cities'),
    where('population', '>', 1_000_000),
    orderBy('population', 'desc'),
    limit(10),
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}

// UPDATE — merge partial fields
export async function updateCity(id, fields) {
  await updateDoc(doc(db, 'cities', id), fields);
}

// DELETE
export async function deleteCity(id) {
  await deleteDoc(doc(db, 'cities', id));
}

// REAL-TIME LISTENER — returns unsubscribe function
export function subscribeToCity(id, callback) {
  return onSnapshot(doc(db, 'cities', id), snap => {
    callback(snap.exists() ? { id: snap.id, ...snap.data() } : null);
  });
}
```

### Pattern 3: Firebase Storage — Upload with Progress (Source: official)

```js
import {
  getStorage, ref, uploadBytesResumable, getDownloadURL, deleteObject,
} from 'firebase/storage';
import app from './firebase';

const storage = getStorage(app);

export function uploadFile(file, path, onProgress) {
  return new Promise((resolve, reject) => {
    const storageRef = ref(storage, path);
    const task = uploadBytesResumable(storageRef, file);

    task.on(
      'state_changed',
      snapshot => {
        const pct = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        onProgress?.(pct);
      },
      reject,
      async () => {
        const url = await getDownloadURL(task.snapshot.ref);
        resolve(url);
      },
    );
  });
}

export async function removeFile(path) {
  await deleteObject(ref(storage, path));
}
```

### Pattern 4: Cloud Functions — HTTPS Callable (Source: official)

```js
// client side
import { getFunctions, httpsCallable } from 'firebase/functions';
import app from './firebase';

const functions = getFunctions(app);

export async function sendWelcomeEmail(userId) {
  const fn = httpsCallable(functions, 'sendWelcomeEmail');
  const result = await fn({ userId });
  return result.data;
}
```

```js
// functions/index.js (deployed to Cloud Functions)
const { onCall, HttpsError } = require('firebase-functions/v2/https');
const { initializeApp } = require('firebase-admin/app');

initializeApp();

exports.sendWelcomeEmail = onCall(async (request) => {
  const { userId } = request.data;
  if (!request.auth) throw new HttpsError('unauthenticated', 'Login required');
  // ... send email logic
  return { success: true };
});
```

### Pattern 5: Error Handling — Firestore Permission Denied (Source: community)

The most common production error: `PERMISSION_DENIED: Missing or insufficient permissions`.
Caused by Firestore Security Rules blocking the request.
Source: SO (~392 votes), GitHub Issues

```js
import { getFirestore, doc, getDoc } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

// BAD — reads before auth state is confirmed; rules require auth
async function unsafeRead(id) {
  const db = getFirestore();
  return getDoc(doc(db, 'private', id)); // may fire before user is authed
}

// GOOD — wait for auth before any protected read
export function safeRead(id) {
  return new Promise((resolve, reject) => {
    const unsub = getAuth().onAuthStateChanged(async user => {
      unsub();
      if (!user) return reject(new Error('Not authenticated'));
      try {
        const snap = await getDoc(doc(getFirestore(), 'private', id));
        resolve(snap.exists() ? snap.data() : null);
      } catch (err) {
        // err.code === 'permission-denied'
        reject(err);
      }
    });
  });
}
```

Minimal Firestore rules for authenticated access:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /cities/{id} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == resource.data.ownerId;
    }
  }
}
```

### Pattern 6: App Check — reCAPTCHA v3 (Source: official)

Prevents unauthorized clients from hitting your Firebase backend.

```js
import { initializeApp } from 'firebase/app';
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check';
import app from './firebase';

// Must be called before any Firebase service is used
initializeAppCheck(app, {
  provider: new ReCaptchaV3Provider(process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY),
  isTokenAutoRefreshEnabled: true,
});
```

## Production Notes

1. **Exposing the API key is safe — but rules are not optional.**
   The Firebase `apiKey` identifies your project and is intentionally public; it is not a secret.
   What protects your data are Firestore/Realtime Database Security Rules and Storage Rules.
   Ship with `allow read, write: if false;` and open only what you need.
   Source: SO (~894 votes)

2. **`initializeApp()` must be called exactly once per app instance.**
   Calling it multiple times (e.g., in hot-module-reload dev environments or Next.js API routes)
   throws `Firebase: No Firebase App '[DEFAULT]' has been created` or duplicate-app errors.
   Guard with:
   ```js
   import { getApps, initializeApp } from 'firebase/app';
   const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
   ```
   Source: SO (~510 votes)

3. **FCM `onMessageReceived` is not called when the app is in the background on Android.**
   Background messages must be handled by a `FirebaseMessagingService` or a service worker
   (`firebase-messaging-sw.js` for web). Data-only messages always go to the background handler;
   notification messages with a `notification` payload are displayed by the system tray and bypass
   `onMessageReceived`.
   Source: SO (~349–590 votes)

4. **Rate limits apply across all auth providers sharing the same project.**
   Enabling email auth and phone/SMS auth means their quotas are shared. A spike in SMS OTP
   traffic can produce `429 Too Many Requests` even when the specific provider being used is
   within its own limits. Monitor per-provider quotas in the Firebase console and request quota
   increases proactively.
   Source: GitHub Issues (67 comments)

5. **Firestore collection `count()` is not a free operation.**
   Before the `count()` aggregate query (added in SDK v9.12), developers iterated all documents
   which caused massive read billing. Use `getCountFromServer(query)` for counted queries; it
   reads only the aggregate, not every document.
   ```js
   import { getCountFromServer, collection } from 'firebase/firestore';
   const snap = await getCountFromServer(collection(db, 'cities'));
   console.log(snap.data().count);
   ```
   Source: SO (~335 votes)

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `PERMISSION_DENIED: Missing or insufficient permissions` | Security Rules deny the request — often because user is not yet authenticated when the call fires | Wait for `onAuthStateChanged` before reads/writes; review and deploy correct Security Rules |
| `No Firebase App '[DEFAULT]' has been created` | `initializeApp()` not called before a service is used, or called in wrong order (SSR, HMR) | Guard with `getApps().length \|\| initializeApp(config)` at module load time |
| FCM notifications not received in background | Notification payload delivered directly by OS/system tray; `onMessage` only fires in foreground | Register `firebase-messaging-sw.js` service worker for web; use `FirebaseMessagingService` on Android |
| `429 Too Many Requests` on auth despite low per-provider traffic | Auth quotas are project-wide across all providers | Separate projects per environment; request quota increase in Firebase console |
| Upload to Storage fails silently or returns 403 | Storage Security Rules require `request.auth != null` but client is unauthenticated | Authenticate user first; check Storage Rules in Firebase console; enable CORS for web uploads |

## Pre-Deploy Checklist

- [ ] All `firebaseConfig` values sourced from environment variables — never hard-coded in committed files
- [ ] Firestore and Storage Security Rules reviewed; default `allow read, write: if false` replaced only with scoped rules
- [ ] `initializeApp()` guarded against duplicate initialization (`getApps().length` check)
- [ ] App Check enabled in production with reCAPTCHA v3 or Device Check (mobile) and enforced in Firebase console
- [ ] Firebase project has separate environments (dev/staging/prod) with separate projects or at minimum separate apps
- [ ] Firestore indexes created for all compound queries (`where` + `orderBy`); missing indexes throw at runtime
- [ ] FCM service worker (`firebase-messaging-sw.js`) deployed alongside app for background notification support

## Troubleshooting

**Error: `PERMISSION_DENIED: Missing or insufficient permissions`**
Cause: Firestore or Storage Security Rules are blocking the request — most often because the user is not authenticated yet when the SDK call is made, or the Rules don't allow the requested operation.
Fix: (1) Wrap all protected reads/writes inside `onAuthStateChanged` callback. (2) Open the Firebase console → Firestore → Rules and use the Rules Playground to simulate the failing request. (3) Deploy rules that explicitly allow the operation for authenticated users.

**Error: `FirebaseError: Firebase: No Firebase App '[DEFAULT]' has been created - call Firebase.initializeApp()`**
Cause: A Firebase service is imported and used before `initializeApp()` runs, or `initializeApp()` is called multiple times in SSR/hot-reload environments.
Fix: Create a single `firebase.js` module that guards initialization with `getApps().length || initializeApp(config)` and import the exported `app` wherever services are needed.

**Error: `FirebaseError: The query requires an index`**
Cause: Firestore compound queries (multiple `where` clauses or `where` + `orderBy`) require a composite index that has not been created.
Fix: Click the link in the error message — it pre-fills the index creation form in the Firebase console. After the index builds (1–5 min), retry the query.

**Error: `auth/too-many-requests` on sign-in**
Cause: Firebase has temporarily blocked sign-in from this device or IP due to repeated failed attempts.
Fix: Wait for the cooldown (usually a few minutes), advise users to reset their password, or use the Firebase console to unblock the account.

## Resources

- Docs: https://firebase.google.com/docs
- Web SDK Setup: https://firebase.google.com/docs/web/setup
- Firestore Security Rules: https://firebase.google.com/docs/firestore/security/get-started
- Upgrade to v9 Modular SDK: https://firebase.google.com/docs/web/modular-upgrade
- GitHub: https://github.com/firebase/firebase-js-sdk
- Firebase Console: https://console.firebase.google.com