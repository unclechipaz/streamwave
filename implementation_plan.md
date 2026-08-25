# Implementation Plan - Refined Landing Page, Checkout & Accessibility

Refine and polish the **StreamWave Entertainment** platform with a full-height landing hero section, enhanced checkout simulation (including explicit decline demonstration and transaction reference displays), complete accessibility features (keyboard focus, screen reader live region status), and full mobile/desktop responsiveness.

---

## User Review Required

> [!IMPORTANT]
> **Simulated Payment States**: The checkout page will now include two explicit action buttons:
> 1. **Simulate Successful Payment** (Primary Red Button) -> Approves payment, generates `SW-DEMO-XXXXX` transaction reference, sets session cookie, and redirects to `/library`.
> 2. **Test Declined Payment** (Secondary Link/Button) -> Demonstrates a simulated payment decline (card/mobile issuer rejection) without setting a cookie or granting library access.

> [!NOTE]
> **Accessibility Improvements**: Adds ARIA live regions (`aria-live="polite"`), explicit focus visible indicators (`:focus-visible`), keyboard support for payment tabs, Escape key modal closing, and `@media (prefers-reduced-motion: reduce)` support.

---

## Proposed Changes

### Backend Refinements

#### [MODIFY] [`app.py`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/app.py)
- Update `DemoPaymentRequest` model:
  ```python
  class DemoPaymentRequest(BaseModel):
      email: str
      method: str
      plan_id: Optional[str] = "streamwave-monthly"
      simulate_decline: Optional[bool] = False
  ```
- In `POST /api/demo-payment`:
  - If `simulate_decline=True`: log structured JSON event (`"status": "declined"`), return HTTP 400 with detail: `"Simulated payment decline: Card or mobile issuer rejected transaction."` without setting session cookie.

---

### Landing Page Refinements

#### [MODIFY] [`public/index.html`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/public/index.html)
- Full-height hero section (`min-height: 92vh`) centered in viewport.
- StreamWave logo on left, restrained "Sign In" button on right.
- Centered main heading, supporting text, email field, and **Get Started ›** button.
- Dark collage artwork backdrop with high-contrast gradient overlay.
- Accessible form labels and ARIA live feedback.

---

### Checkout Refinements

#### [MODIFY] [`public/checkout.html`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/public/checkout.html)
- Display selected payment method steps only after selection.
- Add explicit action buttons:
  - **Simulate Successful Payment** (Primary button)
  - **Test Declined Payment** (Secondary outline button)
- Disable submission buttons while processing to prevent duplicate requests.
- ARIA live region (`role="status" aria-live="polite"`) announcing progress steps to screen readers.
- On success: display generated transaction reference (`SW-DEMO-XXXXX`) in a success state container before redirecting to `/library`.
- On decline: display a clear error state box with retry button.

---

### Styles & Accessibility

#### [MODIFY] [`public/css/styles.css`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/public/css/styles.css)
- Full-height hero layout (`min-height: 92vh`, flexbox centering).
- Explicit high-contrast `:focus-visible` outline (`outline: 2px solid #e50914`).
- `@media (prefers-reduced-motion: reduce)` rules disabling progress animations.
- Ensure strict `overflow-x: hidden` to prevent horizontal scrolling on small screens.

---

### Test Suite Updates

#### [MODIFY] [`tests/test_api.py`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/tests/test_api.py)
- Add test case verifying simulated payment decline (`simulate_decline=True`) returns HTTP 400 and does NOT set a session cookie.

---

## Verification Plan

### Automated Tests
Run pytest in Windows Command Prompt:
```cmd
.venv\Scripts\python.exe -m pytest tests\test_api.py -v
```

### Manual Visitor Journey Verification
1. **Landing Page (`/`)**: Verify full-height hero, logo placement, email entry, and **Get Started ›** click.
2. **Checkout Page (`/checkout`)**:
   - Test EcoCash, Visa, MasterCard tab selections.
   - Click **Test Declined Payment** -> Observe processing animation -> Displays decline state.
   - Click **Simulate Successful Payment** -> Observe processing steps -> Displays `SW-DEMO-XXXXX` transaction ref -> Redirects to `/library`.
3. **Library (`/library`)**:
   - Verify member status bar.
   - Play 5-second movie preview and music sample.
   - Click **Sign Out** -> Confirms cookie cleared and redirects to `/`.
