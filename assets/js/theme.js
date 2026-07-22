(() => {
  const root = document.documentElement;
  root.classList.add('js');

  let savedTheme = null;
  try {
    savedTheme = window.localStorage.getItem('portfolio-theme');
  } catch {
    savedTheme = null;
  }

  const systemTheme = window.matchMedia?.('(prefers-color-scheme: light)').matches
    ? 'light'
    : 'dark';
  const theme = savedTheme === 'light' || savedTheme === 'dark'
    ? savedTheme
    : systemTheme;

  root.dataset.theme = theme;
})();
