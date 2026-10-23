// Light/dark toggle, shared with the blog through localStorage "theme". The page itself is static HTML.
document.getElementById("theme").addEventListener("click", function () {
  var root = document.documentElement;
  var dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
});
