(function () {
  var bar = document.querySelector(".top"),
    links = [].slice.call(document.querySelectorAll("#nav a")),
    sec = document.body.dataset.sec || "home",
    current = "";

  // highlight the current item and slide the menu so it stays in view
  function setNav(id) {
    if (id === current) return;
    current = id;
    links.forEach(function (l) {
      var on = l.getAttribute("data-sec") === id;
      l.classList.toggle("on", on);
      if (on) {
        var n = l.parentNode;
        n.scrollTo({
          left: n.scrollLeft + l.getBoundingClientRect().left - n.getBoundingClientRect().left - (n.clientWidth - l.offsetWidth) / 2,
          behavior: matchMedia("(prefers-reduced-motion:reduce)").matches ? "auto" : "smooth",
        });
      }
    });
  }

  // keep the original CSS size of the name; only shrink it if the longest word would not fit on one line
  function fitName() {
    var h = document.querySelector(".hero h1");
    if (!h) return;
    h.style.fontSize = "";
    var size = parseFloat(getComputedStyle(h).fontSize), w = 0;
    [].forEach.call(h.querySelectorAll("b"), function (b) { w = Math.max(w, b.offsetWidth); });
    if (w > h.clientWidth) h.style.fontSize = Math.floor((size * h.clientWidth) / w) + "px";
  }
  window.addEventListener("resize", fitName);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitName);
  fitName();

  if (sec !== "home") return setNav(sec);

  // home page: follow the scroll position through the sections
  var secs = [].slice.call(document.querySelectorAll("main section")), ticking = false;
  function spy() {
    var y = window.scrollY + bar.offsetHeight + window.innerHeight * 0.25, id = secs[0].id;
    secs.forEach(function (s) { if (s.getBoundingClientRect().top + window.scrollY <= y) id = s.id; });
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) id = secs[secs.length - 1].id;
    setNav(id);
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; requestAnimationFrame(function () { ticking = false; spy(); }); }
  }, { passive: true });
  window.addEventListener("resize", spy);
  spy();
})();
