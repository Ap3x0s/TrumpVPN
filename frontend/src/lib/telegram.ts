// Loads Telegram Login Widget script and renders the button into a container.
//
// IMPORTANT ORDER: Telegram's widget scans the DOM for an element with
// `data-telegram-login` *when the script executes*. So we must set all
// attributes on the container FIRST, then inject the (synchronous) script
// tag right after it. Using async + setting attributes after inject is a
// race the widget reliably loses (no button renders).
export function loadTelegramWidget(containerId: string, botUsername: string, onAuth: (user: unknown) => void) {
  const el = document.getElementById(containerId);
  if (!el) return;

  // 1) global callback used by data-onauth="telegramLogin(user)"
  (window as unknown as { telegramLogin?: (user: unknown) => void }).telegramLogin = (user: unknown) => onAuth(user);

  // 2) prepare the container with all data- attributes BEFORE the script runs
  el.innerHTML = "";
  el.setAttribute("data-telegram-login", botUsername);
  el.setAttribute("data-size", "large");
  el.setAttribute("data-radius", "10");
  el.setAttribute("data-onauth", "telegramLogin(user)");
  el.setAttribute("data-request-access", "write");

  // 3) inject the script synchronously right after the container so it runs
  //    after the attributes above are in the DOM. Avoid re-injecting on re-render.
  const already = document.getElementById("tg-widget-script");
  if (already) already.remove();
  const s = document.createElement("script");
  s.id = "tg-widget-script";
  s.async = false;
  s.src = "https://telegram.org/js/telegram-widget.js?22";
  el.appendChild(s);
}
