# Frontend Documentation

The frontend is an **Angular 19** single-page application that displays a live camera feed with a dark-themed dashboard layout. It uses **Angular Material** for UI components.

## Technology Stack

- **Angular 19** - Standalone components (no NgModules)
- **Angular Material 19** - UI component library (buttons, icons)
- **Angular Animations** - Required by Angular Material
- **TypeScript** - Type-safe development
- **SCSS** - Custom Material theme

## Architecture

The frontend is intentionally simple — a single component that displays an MJPEG video stream from the backend in an `<img>` tag. No WebSocket, no canvas rendering, no JavaScript frame processing. The browser handles MJPEG natively.

```
AppComponent
    │
    ├── <img [src]="streamUrl">     ◄── MJPEG stream from backend
    │
    └── 6x <button mat-flat-button>  ◄── Control buttons (placeholder)
```

## File Structure

```
frontend/src/
├── main.ts                          # Bootstraps AppComponent with appConfig
├── index.html                       # HTML shell, loads Roboto font and Material Icons
├── styles.css                       # Global styles (dark background, Roboto font)
├── custom-theme.scss                # Angular Material dark theme configuration
├── app/
│   ├── app.component.ts             # Root component (stream URL, button definitions)
│   ├── app.component.html           # Template (video panel + button grid)
│   ├── app.component.css            # Dashboard layout styles
│   └── app.config.ts                # App providers (zone change detection, animations)
└── environments/
    ├── environment.ts               # Development config (apiBaseUrl: localhost:8000)
    └── environment.prod.ts          # Production config (apiBaseUrl: '' — same origin)
```

## Component Details

### `AppComponent`

The single component in the application. Standalone (no NgModule).

**Imports**: `MatButtonModule`, `MatIconModule`

**Properties**:
- `streamUrl` — Constructed from `environment.apiBaseUrl` + `/api/video/stream`. Points the `<img>` tag at the backend MJPEG endpoint.
- `buttons` — Array of 6 button definitions, each with a `label` and Material `icon` name:
  - Snapshot (`photo_camera`)
  - Record (`videocam`)
  - Settings (`settings`)
  - Detect (`face`)
  - Fullscreen (`fullscreen`)
  - Info (`info`)

**Note**: The buttons are currently placeholders — they render but have no click handlers or functionality yet.

### Template Layout

The dashboard uses a flexbox layout that fills the full viewport:

```
┌──────────────────────────────────────────────────┐
│                                    ┌──────┬─────┐│
│                                    │Snap- │Direc││
│       Live Camera Feed             │shot  │tory ││
│       (MJPEG Stream)               ├──────┼─────┤│
│                                    │Deli- │Virt.││
│                                    │very  │Key  ││
│                                    ├──────┼─────┤│
│                                    │Full  │     ││
│                                    │screen│Info ││
│                                    └──────┴─────┘│
└──────────────────────────────────────────────────┘
```

- **Left**: Video panel — fills remaining space, black background, rounded corners. The `<img>` tag uses `object-fit: contain` to maintain aspect ratio.
- **Right**: Controls panel — 2-column CSS grid of Material flat buttons with icons. Dark grey buttons (`#3a3a3a`) on a dark grey background (`#2b2b2b`).

## Theming

### Angular Material Theme (`custom-theme.scss`)

Configured as a **dark theme** using Angular Material's `mat.theme()` mixin:

| Property    | Value               |
|-------------|---------------------|
| Theme type  | `dark`              |
| Primary     | `mat.$cyan-palette` |
| Tertiary    | `mat.$blue-palette` |
| Typography  | `Roboto`            |
| Density     | `0` (default)       |

### Global Styles (`styles.css`)

- Body background: `#2b2b2b` (dark grey)
- Font: `Roboto, "Helvetica Neue", sans-serif`
- Full height layout (`html, body { height: 100% }`)

### Component Styles (`app.component.css`)

- Dashboard: `display: flex`, `height: 100vh`, 24px padding and gap
- Video panel: `flex: 1`, black background, 12px border radius
- Control buttons: 120x100px, dark grey (`#3a3a3a`), 12px border radius, 32px icons, lighter on hover (`#4a4a4a`)

## App Configuration (`app.config.ts`)

Providers:
- `provideZoneChangeDetection({ eventCoalescing: true })` — Optimizes change detection by coalescing multiple events.
- `provideAnimationsAsync()` — Enables Angular Material animations (loaded asynchronously).

No router is configured — this is a single-view application.

## Environment Configuration

### Development (`environment.ts`)

```typescript
apiBaseUrl: 'http://localhost:8000'
```

During development, the Angular dev server runs on port 4200 and the `<img>` tag points directly at `http://localhost:8000/api/video/stream`. CORS on the FastAPI backend allows requests from `localhost:4200`.

### Production (`environment.prod.ts`)

```typescript
apiBaseUrl: ''
```

In production, FastAPI serves both the API and the Angular static files from the same origin, so no base URL prefix is needed. The `<img>` tag simply points at `/api/video/stream`.

File replacement is configured in `angular.json` under `configurations.production.fileReplacements` to swap `environment.ts` with `environment.prod.ts` during production builds.

## Testing

Tests use **Jest** with `jest-preset-angular`. All component dependencies (dialogs, services, snackbar) are mocked — no backend required.

### Running tests

```bash
cd frontend

# Run all tests
npm test

# Run a specific test file
npx jest src/app/services/access.service.spec.ts

# Run tests in watch mode
npx jest --watch
```

### Test files

| File | Tests | Coverage |
|------|-------|----------|
| `services/access.service.spec.ts` | 5 | HTTP calls, request bodies, error responses |
| `app.component.spec.ts` | 8 | Component creation, stream URL, buttons, dialog opening |
| `dialogs/keypad-dialog/keypad-dialog.component.spec.ts` | 15 | Key input, backspace, masking, submit, success/error flows |
| `dialogs/update-code-dialog/update-code-dialog.component.spec.ts` | 14 | Validation, submit, success/error flows, error clearing |

### Configuration

- `jest.config.js` — Jest config with `jest-preset-angular` preset
- `setup-jest.ts` — Zone.js and `TestBed.initTestEnvironment()` setup
- `tsconfig.spec.json` — TypeScript config for tests (types: `jest`)

## Build Output

Angular 19 builds to `dist/frontend/browser/` (SSR-compatible directory structure, even with SSR disabled). The `scripts/build.sh` script copies this directory to `backend/static/` so FastAPI can serve it.

## External Resources (loaded via CDN in `index.html`)

- **Roboto font** — `fonts.googleapis.com/css2?family=Roboto:wght@300;400;500`
- **Material Icons** — `fonts.googleapis.com/icon?family=Material+Icons`
