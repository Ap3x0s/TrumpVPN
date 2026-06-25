// Loads Telegram Login Widget script and renders the button into a container.
export function loadTelegramWidget(containerId: string, botUsername: string, onAuth: (user: unknown) => void) {
  const existing = document.getElementById("tg-widget-script");
  if (!existing) {
    const s = document.createElement("script");
    s.id = "tg-widget-script";
    s.async = true;
    s.src = "https://telegram.org/js/telegram-widget.js?22";
    document.body.appendChild(s);
  }
  const el = document.getElementById(containerId);
  if (el) {
    el.setAttribute("data-telegram-login", botUsername);
    el.setAttribute("data-size", "large");
    el.setAttribute("data-radius", "10");
    el.setAttribute("data-onauth", "telegramLogin(user)");
    el.setAttribute("data-request-access", "write");
  }
  // global callback
  (window as unknown as { telegramLogin: (user: unknown) => void }).telegramLogin = (user: unknown) => onAuth(user);
}
