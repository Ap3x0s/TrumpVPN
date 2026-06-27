// Renders the Telegram Login Widget into a container element.
//
// HOW THE WIDGET ACTUALLY WORKS: Telegram's widget script reads the
// `data-telegram-login` (bot username) and other `data-*` attributes from
// the <script> TAG ITSELF, then replaces that script with a button iframe.
// So all attributes must be on the <script>, not on a wrapper div.
//
// data-onauth points to a global function name; we expose it on window.
export function loadTelegramWidget(containerId: string, botUsername: string, onAuth: (user: unknown) => void) {
  const el = document.getElementById(containerId);
  if (!el) return;

  // global callback invoked by the widget as data-onauth="telegramLogin(user)"
  (window as unknown as { telegramLogin?: (user: unknown) => void }).telegramLogin = (user: unknown) => onAuth(user);

  // wipe any previous widget (re-renders / StrictMode double-invoke)
  el.innerHTML = "";

  // all attributes go on the <script> tag itself
  const s = document.createElement("script");
  s.async = true;
  s.src = "https://telegram.org/js/telegram-widget.js?22";
  s.setAttribute("data-telegram-login", botUsername);
  s.setAttribute("data-size", "large");
  s.setAttribute("data-radius", "10");
  s.setAttribute("data-onauth", "telegramLogin(user)");
  s.setAttribute("data-request-access", "write");
  el.appendChild(s);
}
