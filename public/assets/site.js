
(() => {
  const slider = document.querySelector("[data-slider]");
  if (!slider) return;
  const slides = Array.from(slider.querySelectorAll(".slide"));
  const dots = Array.from(slider.querySelectorAll(".slider-dots span"));
  const prev = slider.querySelector("[data-slider-prev]");
  const next = slider.querySelector("[data-slider-next]");
  const interval = Number(slider.dataset.interval || 5000);
  let index = 0;
  let timer = null;
  const applyState = () => {
    const previousIndex = (index - 1 + slides.length) % slides.length;
    const nextIndex = (index + 1) % slides.length;
    slides.forEach((slide, i) => {
      slide.classList.toggle("is-active", i === index);
      slide.classList.toggle("is-prev", i === previousIndex);
      slide.classList.toggle("is-next", i === nextIndex);
    });
    dots.forEach((dot, i) => dot.classList.toggle("is-active", i === index));
  };
  const show = (nextIndex) => {
    index = (nextIndex + slides.length) % slides.length;
    applyState();
  };
  const restart = () => {
    window.clearInterval(timer);
    timer = window.setInterval(() => show(index + 1), interval);
  };
  applyState();
  if (prev) prev.addEventListener("click", () => { show(index - 1); restart(); });
  if (next) next.addEventListener("click", () => { show(index + 1); restart(); });
  timer = window.setInterval(() => show(index + 1), interval);
})();
