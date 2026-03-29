# Facial Recognition — Frontend Design

## Overview

Redesign the **Settings** button flow to navigate to a full settings page (instead of a dialog) where the user can:

1. Reset the access code (existing functionality, moved here).
2. Manage staff face registrations — add, edit, and delete staff members and their photos.

This introduces **Angular routing** to the app for the first time, replacing the previous dialog-based settings with a dedicated page.

## Navigation Flow

```
Dashboard (video + buttons)
    │
    ├── Door Pin button → Keypad dialog (unchanged)
    │
    └── Settings button → navigates to /settings
                              │
                              ├── Access Code section
                              │     └── Update code form (moved from dialog)
                              │
                              └── Staff Management section
                                    │
                                    ├── Staff list (cards/table)
                                    │     └── Click staff → /settings/staff/:id (edit page)
                                    │
                                    └── "Add Staff" button → /settings/staff/new
```

### URL Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `DashboardComponent` | Video feed + control buttons (current app.component content) |
| `/settings` | `SettingsComponent` | Access code + staff list |
| `/settings/staff/new` | `StaffFormComponent` | Register new staff + upload first photo |
| `/settings/staff/:id` | `StaffFormComponent` | Edit staff name + manage photos |

---

## New Components

### 1. `DashboardComponent`

The current `AppComponent` content (video feed + buttons) moves into a dedicated `DashboardComponent`. `AppComponent` becomes a thin shell with just `<router-outlet />`.

```
┌──────────────────────────────────────────────────┐
│                                    ┌──────┬─────┐│
│                                    │Door  │Sett-││
│       Live Camera Feed             │Pin   │ings ││
│       (MJPEG Stream)               ├──────┼─────┤│
│                                    │Snap- │Rec- ││
│                                    │shot  │ord  ││
│                                    ├──────┼─────┤│
│                                    │Full  │     ││
│                                    │screen│Info ││
│                                    └──────┴─────┘│
└──────────────────────────────────────────────────┘
```

The **Settings** button now calls `router.navigate(['/settings'])` instead of opening a dialog.

---

### 2. `SettingsComponent`

Full-page settings view with a back button to return to the dashboard.

```
┌──────────────────────────────────────────────────┐
│  ← Back                          Settings        │
│──────────────────────────────────────────────────│
│                                                  │
│  ┌─ Access Code ───────────────────────────────┐ │
│  │                                             │ │
│  │  Current Code  [________]                   │ │
│  │  New Code      [________]                   │ │
│  │                          [ Update Code ]    │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  ┌─ Staff Management ─────────────────────────┐ │
│  │                                             │ │
│  │  [ + Add New Staff ]                        │ │
│  │                                             │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐    │ │
│  │  │  Alice  │  │  Bob    │  │  Carol  │    │ │
│  │  │  📷 3   │  │  📷 1   │  │  📷 2   │    │ │
│  │  │ [Edit]  │  │ [Edit]  │  │ [Edit]  │    │ │
│  │  └─────────┘  └─────────┘  └─────────┘    │ │
│  │                                             │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

#### Sections

**Access Code** — the same form fields from the old `UpdateCodeDialogComponent`, now inline. Uses `AccessService.updateCode()`.

**Staff Management** — loads staff list from `GET /api/staff` on init.
- Each staff member shown as a Material card with name and photo count.
- "Edit" navigates to `/settings/staff/:id`.
- "+ Add New Staff" navigates to `/settings/staff/new`.

---

### 3. `StaffFormComponent`

Used for both **adding** and **editing** a staff member. The mode is determined by the route parameter:

- `/settings/staff/new` → **Add mode** — name input + photo upload, submit calls `POST /api/staff/register` then `POST /api/staff/{id}/photos`.
- `/settings/staff/:id` → **Edit mode** — loads existing staff data from `GET /api/staff/{id}`, shows name (editable for display), existing photos, and options to add/remove photos.

#### Add Mode

```
┌──────────────────────────────────────────────────┐
│  ← Back                     Add New Staff        │
│──────────────────────────────────────────────────│
│                                                  │
│  Name                                            │
│  ┌──────────────────────────────────────────┐    │
│  │  Alice Johnson                           │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  Photo                                           │
│  ┌──────────────────────────────────────────┐    │
│  │                                          │    │
│  │        [ Choose File ]                   │    │
│  │                                          │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│              [ Cancel ]  [ Submit ]              │
└──────────────────────────────────────────────────┘
```

#### Submit Flow (Add Mode)

1. User enters name and selects a photo file.
2. On submit:
   - Call `POST /api/staff/register` with `{ "name": "Alice Johnson" }`.
   - On success, take the returned `id` and call `POST /api/staff/{id}/photos` with the photo file.
   - If photo upload fails (no face detected), show error but keep the staff registered (user can add photo later).
3. On success → snackbar "Staff member added" → navigate back to `/settings`.

#### Edit Mode

```
┌──────────────────────────────────────────────────┐
│  ← Back                     Edit Staff           │
│──────────────────────────────────────────────────│
│                                                  │
│  Name: Alice Johnson                             │
│                                                  │
│  Photos (3)                                      │
│  ┌────────┐  ┌────────┐  ┌────────┐             │
│  │        │  │        │  │        │             │
│  │ photo  │  │ photo  │  │ photo  │             │
│  │  001   │  │  002   │  │  003   │             │
│  │        │  │        │  │        │             │
│  │  [🗑]  │  │  [🗑]  │  │  [🗑]  │             │
│  └────────┘  └────────┘  └────────┘             │
│                                                  │
│  [ Upload New Photo ]                            │
│                                                  │
│  ──────────────────────────────────────────────  │
│                                                  │
│  [ 🗑 Delete Staff Member ]                      │
│                                                  │
└──────────────────────────────────────────────────┘
```

#### Edit Mode Features

- **View photos**: Display all photos for this staff member as thumbnail cards. Photos are loaded by constructing URLs from the relative paths in the staff record (e.g., `{apiBaseUrl}/data/staff/alice_johnson/photo_001.jpg` — or served via a new static endpoint).
- **Upload new photo**: File picker → `POST /api/staff/{id}/photos`. On success, refresh the photo list.
- **Delete photo**: Each photo has a delete button. Calls a delete action (note: the current backend has `delete_photo` on the store but no API endpoint yet — this will need to be added).
- **Delete staff member**: Danger button at the bottom. Confirmation dialog → `DELETE /api/staff/{id}` → navigate back to `/settings`.

---

## New Service: `StaffService`

```typescript
@Injectable({ providedIn: 'root' })
export class StaffService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  listStaff(): Observable<StaffResponse> {
    return this.http.get<StaffResponse>(`${this.baseUrl}/api/staff`);
  }

  getStaff(staffId: string): Observable<StaffResponse> {
    return this.http.get<StaffResponse>(`${this.baseUrl}/api/staff/${staffId}`);
  }

  registerStaff(name: string): Observable<StaffResponse> {
    return this.http.post<StaffResponse>(`${this.baseUrl}/api/staff/register`, { name });
  }

  deleteStaff(staffId: string): Observable<StaffResponse> {
    return this.http.delete<StaffResponse>(`${this.baseUrl}/api/staff/${staffId}`);
  }

  uploadPhoto(staffId: string, file: File): Observable<StaffResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<StaffResponse>(
      `${this.baseUrl}/api/staff/${staffId}/photos`,
      formData
    );
  }

}

interface StaffResponse {
  status: 'success' | 'error';
  message: string;
  data?: any;
}

interface StaffRecord {
  id: string;
  name: string;
  photos: string[];
  registered_at: string;
}
```

---

## Routing Setup

### `app.routes.ts` (new)

```typescript
import { Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { SettingsComponent } from './settings/settings.component';
import { StaffFormComponent } from './settings/staff-form/staff-form.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'settings', component: SettingsComponent },
  { path: 'settings/staff/new', component: StaffFormComponent },
  { path: 'settings/staff/:id', component: StaffFormComponent },
  { path: '**', redirectTo: '' },
];
```

### `app.config.ts` (updated)

```typescript
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideAnimationsAsync(),
    provideHttpClient(),
    provideRouter(routes),
  ],
};
```

### `app.component.ts` (simplified)

```typescript
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class AppComponent {}
```

---

## Changes to Existing Components

### `AppComponent`

- Becomes a thin router shell: `<router-outlet />` only.
- All dashboard logic moves to `DashboardComponent`.

### `DashboardComponent` (extracted from AppComponent)

- Keeps the video feed + button grid layout.
- **Settings button** now calls `router.navigate(['/settings'])` instead of opening `UpdateCodeDialogComponent`.
- **Door Pin button** still opens the `KeypadDialogComponent` (unchanged).
- Injects `Router` in addition to `MatDialog`.

### `UpdateCodeDialogComponent`

- **Removed as a dialog**. The access code update form is now inline within `SettingsComponent`.
- The same form fields and validation logic are reused, just not wrapped in a dialog.

---

## File Structure

```
frontend/src/app/
├── app.component.ts                    # MODIFIED — thin shell with router-outlet
├── app.component.css                   # MODIFIED — minimal global styles
├── app.routes.ts                       # NEW — route definitions
├── app.config.ts                       # MODIFIED — add provideRouter
├── dashboard/
│   ├── dashboard.component.ts          # NEW — extracted from AppComponent
│   ├── dashboard.component.html        # NEW — video feed + buttons
│   └── dashboard.component.css         # NEW — dashboard layout styles
├── settings/
│   ├── settings.component.ts           # NEW — settings page
│   ├── settings.component.html         # NEW — access code + staff list
│   ├── settings.component.css          # NEW — settings styles
│   └── staff-form/
│       ├── staff-form.component.ts     # NEW — add/edit staff
│       ├── staff-form.component.html   # NEW — name + photos form
│       └── staff-form.component.css    # NEW — staff form styles
├── services/
│   ├── access.service.ts               # UNCHANGED
│   └── staff.service.ts                # NEW — staff CRUD + photo operations
└── dialogs/
    ├── keypad-dialog/                  # UNCHANGED
    └── update-code-dialog/             # DEPRECATED — functionality moved to SettingsComponent
```

---

## Angular Material Components Used

### New imports needed

| Component | Module | Used for |
|-----------|--------|----------|
| Cards | `MatCardModule` | Staff member cards in list |
| List | `MatListModule` | Settings sections |
| Toolbar | `MatToolbarModule` | Page headers with back button |
| Progress spinner | `MatProgressSpinnerModule` | Loading states |
| Divider | `MatDividerModule` | Section separators |

### Existing (reused)

| Component | Module | Used for |
|-----------|--------|----------|
| Button | `MatButtonModule` | Actions (submit, upload, delete) |
| Icon | `MatIconModule` | Back arrow, add, delete, camera icons |
| Form field | `MatFormFieldModule` | Name and code inputs |
| Input | `MatInputModule` | Text/password inputs |
| Snack bar | `MatSnackBarModule` | Success/error notifications |
| Dialog | `MatDialogModule` | Confirmation dialogs (delete staff) |

---

## Styling

All new components follow the existing dark theme:

- Page background: `#2b2b2b`
- Card/section background: `#3a3a3a`
- Text: `#ffffff`
- Accent/primary: Cyan (from Angular Material dark theme)
- Error/danger: `#d32f2f` (red)
- Photo thumbnails: `80x80px` with rounded corners, dark border
- Back button: Material icon button with `arrow_back` icon

---

## User Flows

### Add New Staff

```
User taps "Settings" button on dashboard
    │
    ▼
Settings page loads
    │
    ▼
User taps "+ Add New Staff"
    │
    ▼
Staff form page (add mode)
    │
    ▼
User enters name: "Alice Johnson"
User selects photo file
    │
    ▼
User taps "Submit"
    │
    ├── POST /api/staff/register { name: "Alice Johnson" }
    │   └── 201 → got staff id: "alice_johnson"
    │
    ├── POST /api/staff/alice_johnson/photos [file]
    │   ├── 200 → Face detected, photo saved
    │   └── 400 → "No face detected" → show error, staff still registered
    │
    ▼
Snackbar: "Staff member added"
Navigate back to /settings
Staff list refreshes with new entry
```

### Edit Staff (Add More Photos)

```
User on Settings page → taps "Edit" on Alice's card
    │
    ▼
Staff form page (edit mode) loads
    │
    ├── GET /api/staff/alice_johnson → populates name + photo list
    │
    ▼
User sees existing photos as thumbnails
User taps "Upload New Photo" → file picker
    │
    ▼
POST /api/staff/alice_johnson/photos [file]
    │
    ├── 200 → Photo added → refresh photo list
    └── 400 → "No face detected" → show error
```

### Delete Staff

```
User on edit page → taps "Delete Staff Member"
    │
    ▼
Confirmation dialog: "Delete Alice Johnson? This will remove all photos."
    │
    ├── Cancel → close dialog
    └── Confirm → DELETE /api/staff/alice_johnson
                     │
                     ▼
                  Snackbar: "Staff member removed"
                  Navigate to /settings
```

---

## Backend API Additions Needed

The current backend is missing one endpoint that the frontend needs:

### `DELETE /api/staff/{staff_id}/photos/{photo_index}`

Delete a specific photo from a staff member. The `StaffStore` already has `delete_photo()` but there's no router endpoint for it.

#### Request
```
DELETE /api/staff/alice_johnson/photos/staff/alice_johnson/photo_001.jpg
```

#### Response — 200
```json
{
  "status": "success",
  "message": "Photo removed."
}
```

This endpoint should be added to `backend/routers/staff.py` before implementing the frontend photo deletion feature.

---

## Photo Display

Staff photos are stored at paths like `data/staff/alice_johnson/photo_001.jpg`. To display them in the frontend, the backend needs to serve them. Two options:

### Option A: Static file mount (recommended)

Add a static file mount in `main.py` for the data directory:

```python
data_dir = Path(settings.staff_data_dir) / "staff"
if data_dir.exists():
    app.mount("/api/staff-photos", StaticFiles(directory=data_dir), name="staff-photos")
```

Frontend accesses photos via: `{apiBaseUrl}/api/staff-photos/alice_johnson/photo_001.jpg`

### Option B: Dedicated endpoint

Add a `GET /api/staff/{staff_id}/photos/{filename}` endpoint that reads the file and returns it as `FileResponse`.

**Recommendation:** Option A is simpler and leverages FastAPI's built-in static file serving.
