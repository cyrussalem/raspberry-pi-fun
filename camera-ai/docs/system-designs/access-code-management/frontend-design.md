# Access Code Management — Frontend Design

## Overview

Extend the Angular frontend to interact with the access code management endpoints. Two features are added to the existing dashboard: a keypad for entering access codes to trigger the unlock, and a settings dialog for changing the access code.

## Features

### 1. Access Code Keypad

A numeric keypad overlay or panel where the user enters their access code and submits it to unlock.

#### UI Placement

The **Door Pin** button on the dashboard's right-hand control panel opens a keypad dialog/overlay. This follows the reference UI pattern where "Door Pin" is one of the main action buttons.

#### Keypad Dialog

```
┌─────────────────────────┐
│      Enter Access Code  │
│                         │
│      ┌───────────┐      │
│      │  ● ● ● ●  │      │
│      └───────────┘      │
│                         │
│    ┌───┐ ┌───┐ ┌───┐   │
│    │ 1 │ │ 2 │ │ 3 │   │
│    └───┘ └───┘ └───┘   │
│    ┌───┐ ┌───┐ ┌───┐   │
│    │ 4 │ │ 5 │ │ 6 │   │
│    └───┘ └───┘ └───┘   │
│    ┌───┐ ┌───┐ ┌───┐   │
│    │ 7 │ │ 8 │ │ 9 │   │
│    └───┘ └───┘ └───┘   │
│    ┌───┐ ┌───┐ ┌───┐   │
│    │ ⌫ │ │ 0 │ │ ✓ │   │
│    └───┘ └───┘ └───┘   │
│                         │
│       [ Cancel ]        │
└─────────────────────────┘
```

- Digits are masked as dots (`●`) as the user types.
- Backspace button (`⌫`) removes the last digit.
- Submit button (`✓`) sends the code to `POST /api/access/verify`.
- Cancel button closes the dialog without sending.

#### Response Handling

| Backend Response          | Frontend Behavior                                                   |
|---------------------------|---------------------------------------------------------------------|
| 200 — Access granted      | Show green success snackbar: "Access granted. Door unlocked."       |
| 403 — Invalid code        | Show red error snackbar: "Access denied. Invalid code." Clear input.|
| 429 — Unlock in progress  | Show amber warning snackbar: "Unlock already in progress."          |

After a successful unlock, the dialog closes automatically.

---

### 2. Update Access Code Dialog

A settings dialog for changing the access code.

#### UI Placement

Accessed from the **Settings** button on the dashboard control panel. Opens a Material dialog with two input fields.

#### Update Dialog

```
┌──────────────────────────────┐
│    Update Access Code        │
│                              │
│  Current Code                │
│  ┌──────────────────────┐    │
│  │  ● ● ● ●             │    │
│  └──────────────────────┘    │
│                              │
│  New Code                    │
│  ┌──────────────────────┐    │
│  │  ● ● ● ● ● ●         │    │
│  └──────────────────────┘    │
│                              │
│   [ Cancel ]  [ Update ]     │
└──────────────────────────────┘
```

- Both fields use `type="password"` to mask input.
- **Update** button sends `POST /api/access/update` with `{ current_code, new_code }`.
- Validation: new code must be 4+ digits, numeric only (validated client-side before sending).

#### Response Handling

| Backend Response            | Frontend Behavior                                                 |
|-----------------------------|-------------------------------------------------------------------|
| 200 — Code updated          | Show green snackbar: "Access code updated." Close dialog.         |
| 403 — Wrong current code    | Show error under the current code field. Do not close dialog.     |
| 422 — Validation error      | Show error under the new code field.                              |

---

## New Components

### `KeypadDialogComponent`

Standalone component displayed as a Material Dialog (`MatDialog`).

- **Inputs**: None (self-contained).
- **Outputs**: Closes with result `true` on successful unlock, `undefined` on cancel.
- **Angular Material imports**: `MatDialogModule`, `MatButtonModule`, `MatIconModule`, `MatSnackBarModule`.
- **State**: `enteredCode: string` — built up digit by digit from button presses.

### `UpdateCodeDialogComponent`

Standalone component displayed as a Material Dialog.

- **Inputs**: None.
- **Outputs**: Closes with result `true` on successful update, `undefined` on cancel.
- **Angular Material imports**: `MatDialogModule`, `MatButtonModule`, `MatFormFieldModule`, `MatInputModule`, `MatSnackBarModule`.
- **State**: `currentCode: string`, `newCode: string`, `error: string | null`.

### `AccessService`

Angular service that handles HTTP calls to the backend access endpoints.

```typescript
@Injectable({ providedIn: 'root' })
export class AccessService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  verifyCode(code: string): Observable<AccessResponse> {
    return this.http.post<AccessResponse>(`${this.baseUrl}/api/access/verify`, { code });
  }

  updateCode(currentCode: string, newCode: string): Observable<AccessResponse> {
    return this.http.post<AccessResponse>(`${this.baseUrl}/api/access/update`, {
      current_code: currentCode,
      new_code: newCode,
    });
  }
}

interface AccessResponse {
  status: 'success' | 'error';
  message: string;
}
```

---

## Changes to Existing Components

### `AppComponent`

- Update the `buttons` array to wire click handlers to the "Door Pin" and "Settings" buttons.
- Add `MatDialog` injection to open the keypad and update dialogs.
- Add `MatSnackBar` injection for showing response notifications.
- Add `HttpClientModule` (or `provideHttpClient()`) to app config providers.

```typescript
// In app.component.ts
onButtonClick(label: string): void {
  switch (label) {
    case 'Door Pin':
      this.dialog.open(KeypadDialogComponent);
      break;
    case 'Settings':
      this.dialog.open(UpdateCodeDialogComponent);
      break;
  }
}
```

### Button Updates

Replace current placeholder buttons with feature-specific ones:

```typescript
readonly buttons = [
  { label: 'Door Pin', icon: 'dialpad' },
  { label: 'Settings', icon: 'settings' },
  // ... other buttons as needed
];
```

### `app.config.ts`

Add `provideHttpClient()` to the providers array:

```typescript
import { provideHttpClient } from '@angular/common/http';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideAnimationsAsync(),
    provideHttpClient(),
  ],
};
```

---

## Styling

Both dialogs follow the existing dark theme:

- Dialog background: `#2b2b2b` (matching dashboard)
- Keypad buttons: `#3a3a3a` with white text (matching control buttons)
- Submit/confirm buttons: Cyan (primary theme color)
- Error text: Material warn color (red)
- Success snackbar: Green background
- Error snackbar: Red background

---

## File Structure

New files:

```
frontend/src/app/
├── dialogs/
│   ├── keypad-dialog/
│   │   ├── keypad-dialog.component.ts
│   │   ├── keypad-dialog.component.html
│   │   └── keypad-dialog.component.css
│   └── update-code-dialog/
│       ├── update-code-dialog.component.ts
│       ├── update-code-dialog.component.html
│       └── update-code-dialog.component.css
└── services/
    └── access.service.ts
```

---

## User Flow

### Unlock Flow

```
User taps "Door Pin" button
    │
    ▼
Keypad dialog opens
    │
    ▼
User enters code via number pad
    │
    ▼
User taps ✓ (submit)
    │
    ├── Code correct → Green snackbar → Dialog closes → GPIO unlocks for 5s
    │
    └── Code wrong → Red snackbar → Input clears → Dialog stays open
```

### Update Code Flow

```
User taps "Settings" button
    │
    ▼
Update code dialog opens
    │
    ▼
User enters current code + new code
    │
    ▼
User taps "Update"
    │
    ├── Current code correct → Green snackbar → Dialog closes
    │
    └── Current code wrong → Error shown under field → Dialog stays open
```
