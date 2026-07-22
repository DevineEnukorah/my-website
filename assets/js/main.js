(() => {
  'use strict';

  const root = document.documentElement;
  const body = document.body;
  const header = document.querySelector('[data-header]');
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const menuToggle = document.querySelector('[data-menu-toggle]');
  const mobileNav = document.querySelector('[data-mobile-nav]');
  const backToTop = document.querySelector('[data-back-to-top]');
  const copyButton = document.querySelector('[data-copy-email]');
  const copyLabel = document.querySelector('[data-copy-label]');
  const copyStatus = document.querySelector('[data-copy-status]');
  const year = document.querySelector('[data-current-year]');
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  const setTheme = (theme, persist = true) => {
    const normalizedTheme = theme === 'light' ? 'light' : 'dark';
    root.dataset.theme = normalizedTheme;

    if (themeToggle) {
      const isDark = normalizedTheme === 'dark';
      themeToggle.setAttribute('aria-pressed', String(isDark));
      themeToggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
      themeToggle.title = isDark ? 'Switch to light theme' : 'Switch to dark theme';
    }

    if (persist) {
      try {
        window.localStorage.setItem('portfolio-theme', normalizedTheme);
      } catch {
        // Theme persistence is optional. The site remains fully functional.
      }
    }
  };

  setTheme(root.dataset.theme, false);

  themeToggle?.addEventListener('click', () => {
    setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
  });

  const closeMenu = () => {
    if (!menuToggle || !mobileNav) return;
    menuToggle.setAttribute('aria-expanded', 'false');
    menuToggle.setAttribute('aria-label', 'Open navigation');
    mobileNav.hidden = true;
    body.classList.remove('menu-open');
  };

  const openMenu = () => {
    if (!menuToggle || !mobileNav) return;
    menuToggle.setAttribute('aria-expanded', 'true');
    menuToggle.setAttribute('aria-label', 'Close navigation');
    mobileNav.hidden = false;
    body.classList.add('menu-open');
  };

  menuToggle?.addEventListener('click', () => {
    const isOpen = menuToggle.getAttribute('aria-expanded') === 'true';
    isOpen ? closeMenu() : openMenu();
  });

  mobileNav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', closeMenu);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth >= 800) closeMenu();
  }, { passive: true });

  const revealElements = document.querySelectorAll('.reveal');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealElements.forEach((element) => element.classList.add('is-visible'));
  } else {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -48px' });

    revealElements.forEach((element) => revealObserver.observe(element));
  }

  const primaryLinks = document.querySelectorAll('.desktop-nav a');
  const sections = [...primaryLinks]
    .map((link) => document.querySelector(link.hash))
    .filter(Boolean);

  if ('IntersectionObserver' in window && sections.length) {
    const sectionObserver = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

      if (!visible) return;
      primaryLinks.forEach((link) => {
        const active = link.hash === `#${visible.target.id}`;
        link.classList.toggle('is-active', active);
        if (active) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, { rootMargin: '-30% 0px -55%', threshold: [0.01, 0.25, 0.5] });

    sections.forEach((section) => sectionObserver.observe(section));
  }

  const updateScrollState = () => {
    const isScrolled = window.scrollY > 24;
    header?.classList.toggle('is-scrolled', isScrolled);
    backToTop?.classList.toggle('is-visible', window.scrollY > 650);
  };

  updateScrollState();
  window.addEventListener('scroll', updateScrollState, { passive: true });

  copyButton?.addEventListener('click', async () => {
    const email = copyButton.dataset.email;
    if (!email) return;

    try {
      await navigator.clipboard.writeText(email);
      copyButton.classList.add('is-copied');
      if (copyLabel) copyLabel.textContent = 'Email copied';
      if (copyStatus) copyStatus.textContent = 'Email address copied to clipboard.';

      window.setTimeout(() => {
        copyButton.classList.remove('is-copied');
        if (copyLabel) copyLabel.textContent = 'Copy email';
        if (copyStatus) copyStatus.textContent = '';
      }, 2200);
    } catch {
      window.location.href = `mailto:${email}`;
    }
  });

  if (year) year.textContent = String(new Date().getFullYear());
})();
