(() => {
  // Configurable WebSocket URL (replace as needed)
  const wsBaseUrl = window.location.origin.replace(/^http/, 'ws') + '/api/proxy/ws_service/';

  let ws;
  let reconnectInterval = 3000; // milliseconds
  let reconnectTimer = null;

  // Initialize WebSocket connection with auto reconnect
  function initWebSocket() {
    ws = new WebSocket(wsBaseUrl);

    ws.onopen = () => {
      console.log("WebSocket connected");
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("WS message received:", msg);
        // Implement message handling here if needed
      } catch (e) {
        console.warn("Invalid WebSocket message:", e);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    ws.onclose = () => {
      console.log("WebSocket closed, reconnecting in 3s...");
      reconnectTimer = setTimeout(initWebSocket, reconnectInterval);
    };
  }

  initWebSocket();

  // Helper: get all visible and focusable elements
  function getFocusableElements() {
    return Array.from(document.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    ))
    .filter(el => el.offsetParent !== null && !el.disabled && isVisible(el));
  }

  // Check element is visible in DOM (works well in most cases)
  function isVisible(element) {
    return !!( element.offsetWidth || element.offsetHeight || element.getClientRects().length );
  }

  // Spatial navigation — find the next element visually in the direction
  function findNextElement(currentEl, elements, direction) {
    if (!currentEl) return elements[0] || null;

    const rect = currentEl.getBoundingClientRect();
    const currentCenter = {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2,
    };

    // Filter candidates in the right direction
    const candidates = elements.filter(el => {
      if (el === currentEl) return false;
      const elRect = el.getBoundingClientRect();
      const elCenter = {
        x: elRect.left + elRect.width / 2,
        y: elRect.top + elRect.height / 2,
      };

      switch (direction) {
        case 'up':
          return elCenter.y < currentCenter.y;
        case 'down':
          return elCenter.y > currentCenter.y;
        case 'left':
          return elCenter.x < currentCenter.x;
        case 'right':
          return elCenter.x > currentCenter.x;
        default:
          return false;
      }
    });

    if (candidates.length === 0) return null;

    function distance(a, b) {
      return Math.sqrt(Math.pow(a.x - b.x,2) + Math.pow(a.y - b.y,2));
    }

    // Weight distance orthogonal to direction to prefer straight navigation
    const weightedDistance = (candidateCenter) => {
      switch (direction) {
        case 'up':
        case 'down':
          return distance(currentCenter, candidateCenter) + Math.abs(candidateCenter.x - currentCenter.x) * 10;
        case 'left':
        case 'right':
          return distance(currentCenter, candidateCenter) + Math.abs(candidateCenter.y - currentCenter.y) * 10;
      }
    };

    let bestEl = null;
    let bestDist = Infinity;
    for (const el of candidates) {
      const elRect = el.getBoundingClientRect();
      const elCenter = {
        x: elRect.left + elRect.width / 2,
        y: elRect.top + elRect.height / 2,
      };
      let dist = weightedDistance(elCenter);
      if (dist < bestDist) {
        bestDist = dist;
        bestEl = el;
      }
    }
    return bestEl;
  }

  // Check if element is input-like or interactive and should trap native key handling
  function isInputLike(el) {
    const tag = el.tagName.toUpperCase();
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return true;

    const role = el.getAttribute('role');
    if (role && ['slider', 'spinbutton', 'textbox'].includes(role.toLowerCase())) return true;

    // Additional check for contentEditable elements
    if (el.isContentEditable) return true;

    return false;
  }

  let currentFocusedElement = null;

  function focusElement(el) {
    if (!el) return;
    try {
      el.focus();
      currentFocusedElement = el;
    } catch (e) {
      console.warn("Cannot focus element", e);
    }
  }

  window.addEventListener('keydown', (event) => {
    const active = document.activeElement;

    // Let native controls handle keys inside inputs, selects, sliders, contenteditable
    if (isInputLike(active)) {
      return;
    }

    const focusables = getFocusableElements();

    if (!focusables.length) return;

    if (!currentFocusedElement || !document.contains(currentFocusedElement)) {
      if (active && focusables.includes(active)) {
        currentFocusedElement = active;
      } else {
        focusElement(focusables[0]);
        event.preventDefault();
        return;
      }
    }

    let nextElement;

    switch (event.key) {
      case 'ArrowUp':
        nextElement = findNextElement(currentFocusedElement, focusables, 'up');
        break;
      case 'ArrowDown':
        nextElement = findNextElement(currentFocusedElement, focusables, 'down');
        break;
      case 'ArrowLeft':
        nextElement = findNextElement(currentFocusedElement, focusables, 'left');
        break;
      case 'ArrowRight':
        nextElement = findNextElement(currentFocusedElement, focusables, 'right');
        break;
      case 'Enter':
        if (currentFocusedElement) {
          currentFocusedElement.click();
          event.preventDefault();
        }
        return;
      // Additional keys commonly used on remotes:
      case 'Play':
      case 'MediaPlayPause':
      case ' ':
        // Simulate space for play/pause toggle
        if (active) {
          active.dispatchEvent(new KeyboardEvent('keydown', {code: 'Space', key: ' ', bubbles: true}));
          active.dispatchEvent(new KeyboardEvent('keyup', {code: 'Space', key: ' ', bubbles: true}));
          event.preventDefault();
        }
        return;
      case 'Backspace': // Some devices may still send backspace for back
      case 'BrowserBack':
        if (window.history.length > 1) {
          window.history.back();
          event.preventDefault();
        }
        return;
      default:
        return;
    }

    if (nextElement) {
      focusElement(nextElement);
      event.preventDefault();
    }
  });

  // Watch for DOM changes to keep focus manageable
  const observer = new MutationObserver(() => {
    if (currentFocusedElement && !document.contains(currentFocusedElement)) {
      currentFocusedElement = null;
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Initialize focus on page load
  document.addEventListener('DOMContentLoaded', () => {
    const focusables = getFocusableElements();
    if (focusables.length) {
      focusElement(focusables[0]);
    }
  });
})();