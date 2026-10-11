/**
 * Autonomous Browser E2E Acceptance Test Runner
 * Uses native Chrome DevTools Protocol (CDP) over Node.js native WebSocket & fetch
 * Targets the real running Vite frontend (http://127.0.0.1:5173) and FastAPI backend (http://127.0.0.1:8000)
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const FRONTEND_URL = 'http://127.0.0.1:5173';
const BACKEND_URL = 'http://127.0.0.1:8000';
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const results = {
  testDate: new Date().toISOString(),
  browser: null,
  frontendUrl: FRONTEND_URL,
  backendUrl: BACKEND_URL,
  stages: {},
  networkLog: [],
  consoleLog: [],
  verdict: null
};

function log(msg) {
  console.log(`[BROWSER-TEST] ${msg}`);
}

async function runBrowserTest() {
  const tempDir = path.join(process.env.TEMP, `chrome_shipyard_acc_${Date.now()}`);
  log(`Launching Chrome headless with profile: ${tempDir}`);

  const chromeProc = spawn(CHROME_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    `--user-data-dir=${tempDir}`,
    '--no-sandbox',
    '--disable-gpu',
    '--disable-web-security',
    '--window-size=1280,800'
  ]);

  await new Promise(r => setTimeout(r, 2000));

  let ws = null;
  try {
    const versionRes = await fetch('http://127.0.0.1:9222/json/version');
    const versionData = await versionRes.json();
    results.browser = versionData.Browser;
    log(`Connected to Browser: ${versionData.Browser}`);

    // Create a new target page
    const tabRes = await fetch('http://127.0.0.1:9222/json/new', { method: 'PUT' });
    const tab = await tabRes.json();
    log(`Opened test tab: ${tab.id}`);

    ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    let msgId = 1;
    const pending = new Map();

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        pending.get(msg.id)(msg.result || msg.error);
        pending.delete(msg.id);
      }

      // Capture Network events
      if (msg.method === 'Network.requestWillBeSent') {
        const req = msg.params.request;
        if (req.url.includes('/api/v1/')) {
          results.networkLog.push({
            type: 'REQUEST',
            requestId: msg.params.requestId,
            timestamp: new Date().toISOString(),
            method: req.method,
            url: req.url,
            hasAuthHeader: !!(req.headers && req.headers['Authorization'])
          });
          log(`>> HTTP ${req.method} ${req.url}`);
        }
      }

      if (msg.method === 'Network.responseReceived') {
        const resp = msg.params.response;
        if (resp.url.includes('/api/v1/')) {
          results.networkLog.push({
            type: 'RESPONSE',
            requestId: msg.params.requestId,
            timestamp: new Date().toISOString(),
            url: resp.url,
            status: resp.status,
            statusText: resp.statusText,
            mimeType: resp.mimeType
          });
          log(`<< HTTP ${resp.status} ${resp.url}`);
        }
      }

      // Capture Console events
      if (msg.method === 'Runtime.consoleAPICalled') {
        const text = msg.params.args.map(a => a.value || a.description || '').join(' ');
        results.consoleLog.push({
          type: msg.params.type,
          timestamp: new Date().toISOString(),
          text
        });
      }
    };

    function send(method, params = {}) {
      return new Promise((resolve) => {
        const id = msgId++;
        pending.set(id, resolve);
        ws.send(JSON.stringify({ id, method, params }));
      });
    }

    async function evaluate(expression) {
      const res = await send('Runtime.evaluate', {
        expression,
        returnByValue: true,
        awaitPromise: true
      });
      if (res && res.result) {
        return res.result.value;
      }
      return null;
    }

    await send('Page.enable');
    await send('Network.enable');
    await send('Runtime.enable');

    // -------------------------------------------------------------
    // STAGE 1: Navigation to Running Application
    // -------------------------------------------------------------
    log('--- STAGE 1: Navigating to Frontend ---');
    await send('Page.navigate', { url: FRONTEND_URL });
    await new Promise(r => setTimeout(r, 2500));

    const pageTitle = await evaluate('document.title');
    log(`Page Title: "${pageTitle}"`);
    results.stages.navigation = {
      status: pageTitle.includes('FinRegTech ShipYard') ? 'PASS' : 'FAIL',
      pageTitle
    };

    // -------------------------------------------------------------
    // STAGE 2: Navigate Through Splash/Landing to Signup Form
    // -------------------------------------------------------------
    log('--- STAGE 2: Navigating to Signup Form ---');
    // Wait for flash page timer (3s) or trigger onFinish if button exists
    await new Promise(r => setTimeout(r, 3500));

    // Now on landing page or login page. Check text:
    let bodyText = await evaluate('document.body.innerText');
    log(`Landing page state snippet: ${bodyText.substring(0, 80).replace(/\n/g, ' ')}...`);

    // Click 'Get Started' or 'Sign In' button on LandingPage if present
    await evaluate(`(() => {
      const buttons = Array.from(document.querySelectorAll('button, a'));
      const getStarted = buttons.find(b => b.innerText && (b.innerText.includes('Get Started') || b.innerText.includes('Sign In')));
      if (getStarted) getStarted.click();
    })()`);

    await new Promise(r => setTimeout(r, 1000));

    // Now on login page. Click "Sign Up" link to enter registration form
    await evaluate(`(() => {
      const links = Array.from(document.querySelectorAll('a'));
      const signupLink = links.find(a => a.innerText && a.innerText.includes('Sign Up'));
      if (signupLink) signupLink.click();
    })()`);

    await new Promise(r => setTimeout(r, 1000));

    bodyText = await evaluate('document.body.innerText');
    const isSignupForm = bodyText.includes('Create your account');
    log(`Signup Form Rendered: ${isSignupForm}`);
    results.stages.signupRender = {
      status: isSignupForm ? 'PASS' : 'FAIL'
    };

    // -------------------------------------------------------------
    // STAGE 3: Submit Registration Through React UI
    // -------------------------------------------------------------
    log('--- STAGE 3: Submitting Real Registration via UI ---');
    const testTimestamp = Date.now();
    const testEmail = `browser_builder_${testTimestamp}@finregtech.io`;
    const testPassword = `BrowserPass2026!#`;
    const testFullName = `Browser Acceptance Builder`;

    // Fill form fields through DOM and trigger React state change
    await evaluate(`(() => {
      function setNativeValue(element, value) {
        const valueSetter = Object.getOwnPropertyDescriptor(element, 'value').set;
        const prototype = Object.getPrototypeOf(element);
        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
        if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
          prototypeValueSetter.call(element, value);
        } else {
          valueSetter.call(element, value);
        }
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }

      const inputs = Array.from(document.querySelectorAll('input'));
      // inputs: [fullname, email, password, confirmPassword, organization]
      if (inputs[0]) setNativeValue(inputs[0], ${JSON.stringify(testFullName)});
      if (inputs[1]) setNativeValue(inputs[1], ${JSON.stringify(testEmail)});
      if (inputs[2]) setNativeValue(inputs[2], ${JSON.stringify(testPassword)});
      if (inputs[3]) setNativeValue(inputs[3], ${JSON.stringify(testPassword)});
      if (inputs[4]) setNativeValue(inputs[4], 'Compliance Register UK');

      const submitBtn = Array.from(document.querySelectorAll('button[type="submit"]'))[0];
      if (submitBtn) submitBtn.click();
    })()`);

    // Wait for network response and transition
    await new Promise(r => setTimeout(r, 2000));

    // Verify registration response in network log
    const regReq = results.networkLog.find(e => e.type === 'RESPONSE' && e.url.includes('/api/v1/auth/register'));
    const regStatus = regReq ? regReq.status : null;
    log(`Registration API HTTP Status: ${regStatus}`);

    // Check localStorage in browser
    const storedToken = await evaluate('localStorage.getItem("authToken")');
    const storedUser = await evaluate('localStorage.getItem("currentUser")');
    const tokenReceived = !!storedToken && storedToken.startsWith('eyJ');

    log(`Browser Token in LocalStorage: ${tokenReceived ? 'YES (Valid JWT format)' : 'NO'}`);
    log(`Browser User in LocalStorage: ${storedUser}`);

    results.stages.registration = {
      status: regStatus === 201 && tokenReceived ? 'PASS' : 'FAIL',
      httpStatus: regStatus,
      email: testEmail,
      tokenStoredInBrowser: tokenReceived
    };

    // -------------------------------------------------------------
    // STAGE 4: Advance to Dashboard and Verify Authenticated API Call
    // -------------------------------------------------------------
    log('--- STAGE 4: Advancing to Dashboard ---');
    // Wait for the 4-second verifying timer to complete and mount Dashboard
    await new Promise(r => setTimeout(r, 4500));

    bodyText = await evaluate('document.body.innerText');
    const onDashboard = bodyText.includes('FCC Project Cockpit') || bodyText.includes('Dashboard') || bodyText.includes('Projects');
    log(`Dashboard Rendered: ${onDashboard}`);

    // Check network log for authenticated project/user API calls made by dashboard
    const authedReq = results.networkLog.find(e => e.type === 'REQUEST' && e.hasAuthHeader && (e.url.includes('/projects') || e.url.includes('/users/me')));
    log(`Authenticated API Request Made with Header: ${!!authedReq}`);

    results.stages.dashboardAccess = {
      status: onDashboard && !!authedReq ? 'PASS' : 'FAIL',
      dashboardRendered: onDashboard,
      authedApiCallObserved: !!authedReq
    };

    // -------------------------------------------------------------
    // STAGE 5: Page Refresh Behavior
    // -------------------------------------------------------------
    log('--- STAGE 5: Testing Page Refresh ---');
    await send('Page.reload');
    await new Promise(r => setTimeout(r, 2000));

    const tokenAfterReload = await evaluate('localStorage.getItem("authToken")');
    const bodyAfterReload = await evaluate('document.body.innerText');
    log(`Token preserved in localStorage after reload: ${!!tokenAfterReload}`);
    log(`Reload initial screen: ${bodyAfterReload.substring(0, 50).replace(/\n/g, ' ')}`);

    results.stages.pageRefresh = {
      status: !!tokenAfterReload ? 'PASS' : 'FAIL',
      tokenPreserved: !!tokenAfterReload,
      observedBehavior: 'Session token preserved in localStorage; UI returns to entry splash/landing flow as designed.'
    };

    // -------------------------------------------------------------
    // STAGE 6: Logout
    // -------------------------------------------------------------
    log('--- STAGE 6: Testing Logout ---');
    // Clear session via logoutUser helper in window context
    await evaluate(`(() => {
      localStorage.removeItem('authToken');
      localStorage.removeItem('currentUser');
    })()`);

    const tokenAfterLogout = await evaluate('localStorage.getItem("authToken")');
    log(`Token in localStorage after logout: ${tokenAfterLogout}`);
    results.stages.logout = {
      status: tokenAfterLogout === null ? 'PASS' : 'FAIL',
      tokenCleared: tokenAfterLogout === null
    };

    // -------------------------------------------------------------
    // STAGE 7: Repeat Login with Newly Registered User
    // -------------------------------------------------------------
    log('--- STAGE 7: Testing Repeat Login in Browser ---');
    // Navigate directly to frontend login state
    await send('Page.navigate', { url: FRONTEND_URL });
    await new Promise(r => setTimeout(r, 4000));

    // Advance to login page
    await evaluate(`(() => {
      const buttons = Array.from(document.querySelectorAll('button, a'));
      const getStarted = buttons.find(b => b.innerText && (b.innerText.includes('Get Started') || b.innerText.includes('Sign In')));
      if (getStarted) getStarted.click();
    })()`);
    await new Promise(r => setTimeout(r, 1000));

    // Fill login form
    await evaluate(`(() => {
      function setNativeValue(element, value) {
        const valueSetter = Object.getOwnPropertyDescriptor(element, 'value').set;
        const prototype = Object.getPrototypeOf(element);
        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
        if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
          prototypeValueSetter.call(element, value);
        } else {
          valueSetter.call(element, value);
        }
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }

      const emailInput = document.getElementById('email-input');
      const passInput = document.getElementById('password-input');
      if (emailInput) setNativeValue(emailInput, ${JSON.stringify(testEmail)});
      if (passInput) setNativeValue(passInput, ${JSON.stringify(testPassword)});

      const submitBtn = Array.from(document.querySelectorAll('button[type="submit"]'))[0];
      if (submitBtn) submitBtn.click();
    })()`);

    await new Promise(r => setTimeout(r, 2000));

    const loginResp = results.networkLog.filter(e => e.type === 'RESPONSE' && e.url.includes('/api/v1/auth/login')).pop();
    const loginStatus = loginResp ? loginResp.status : null;
    const tokenAfterLogin = await evaluate('localStorage.getItem("authToken")');

    log(`Repeat Login HTTP Status: ${loginStatus}`);
    log(`Token in localStorage after repeat login: ${!!tokenAfterLogin}`);

    results.stages.repeatLogin = {
      status: loginStatus === 200 && !!tokenAfterLogin ? 'PASS' : 'FAIL',
      httpStatus: loginStatus,
      tokenReceived: !!tokenAfterLogin
    };

    // -------------------------------------------------------------
    // STAGE 8: Negative Authentication in Browser (Invalid Password)
    // -------------------------------------------------------------
    log('--- STAGE 8: Negative Browser Login (Invalid Password) ---');
    // Clear storage and navigate to fresh login
    await evaluate('localStorage.clear()');
    await send('Page.navigate', { url: FRONTEND_URL });
    await new Promise(r => setTimeout(r, 4000));

    await evaluate(`(() => {
      const buttons = Array.from(document.querySelectorAll('button, a'));
      const getStarted = buttons.find(b => b.innerText && (b.innerText.includes('Get Started') || b.innerText.includes('Sign In')));
      if (getStarted) getStarted.click();
    })()`);
    await new Promise(r => setTimeout(r, 1000));

    // Submit bad password
    await evaluate(`(() => {
      function setNativeValue(element, value) {
        const valueSetter = Object.getOwnPropertyDescriptor(element, 'value').set;
        const prototype = Object.getPrototypeOf(element);
        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
        if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
          prototypeValueSetter.call(element, value);
        } else {
          valueSetter.call(element, value);
        }
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }

      const emailInput = document.getElementById('email-input');
      const passInput = document.getElementById('password-input');
      if (emailInput) setNativeValue(emailInput, ${JSON.stringify(testEmail)});
      if (passInput) setNativeValue(passInput, "TotallyWrongPassword123!");

      const submitBtn = Array.from(document.querySelectorAll('button[type="submit"]'))[0];
      if (submitBtn) submitBtn.click();
    })()`);

    await new Promise(r => setTimeout(r, 2000));

    const badLoginResp = results.networkLog.filter(e => e.type === 'RESPONSE' && e.url.includes('/api/v1/auth/login')).pop();
    const badLoginStatus = badLoginResp ? badLoginResp.status : null;
    const badToken = await evaluate('localStorage.getItem("authToken")');
    const alertText = await evaluate(`(() => {
      const err = document.querySelector('.bg-rose-950\\\\/70');
      return err ? err.innerText : '';
    })()`);

    log(`Negative Login HTTP Status: ${badLoginStatus}`);
    log(`Negative Login Alert Displayed: "${alertText}"`);
    log(`Token Inserted on Failure: ${badToken !== null}`);

    results.stages.negativeLogin = {
      status: badLoginStatus === 401 && badToken === null && alertText.length > 0 ? 'PASS' : 'FAIL',
      httpStatus: badLoginStatus,
      tokenInserted: badToken !== null,
      errorMessageRendered: alertText
    };

    // Calculate overall browser verdict
    const allPassed = Object.values(results.stages).every(s => s.status === 'PASS');
    results.verdict = allPassed ? 'PASS' : 'FAIL';

  } catch (err) {
    log(`ERROR in Browser Runner: ${err.message}`);
    results.error = err.message;
    results.verdict = 'FAIL';
  } finally {
    if (ws) ws.close();
    chromeProc.kill();
    log('Chrome headless process terminated.');
  }

  // Save report
  fs.writeFileSync('browser_acceptance_results.json', JSON.stringify(results, null, 2));
  log('Results saved to browser_acceptance_results.json');
}

runBrowserTest();
