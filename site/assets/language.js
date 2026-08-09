(() => {
  const STORAGE_KEY = 'notification-sound-db.language';
  const SUPPORTED_LANGUAGES = new Set(['en', 'ja']);
  const currentLanguage = document.documentElement.lang.split('-')[0].toLocaleLowerCase();

  const storedLanguage = () => {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return SUPPORTED_LANGUAGES.has(value) ? value : null;
    } catch {
      return null;
    }
  };

  const browserLanguage = () => {
    const preferences = navigator.languages?.length
      ? navigator.languages
      : [navigator.language || 'en'];
    for (const preference of preferences) {
      const language = preference.split('-')[0].toLocaleLowerCase();
      if (SUPPORTED_LANGUAGES.has(language)) return language;
    }
    return 'en';
  };

  const rememberLanguage = (language) => {
    if (!SUPPORTED_LANGUAGES.has(language)) return;
    try {
      localStorage.setItem(STORAGE_KEY, language);
    } catch {
      // Continue with normal navigation when storage is unavailable.
    }
  };

  const preferredLanguage = storedLanguage() || browserLanguage();
  if (preferredLanguage !== currentLanguage) {
    const alternate = document.querySelector(
      `link[rel="alternate"][hreflang="${preferredLanguage}"]`,
    );
    if (alternate) {
      const destination = new URL(alternate.href, window.location.href);
      destination.search = window.location.search;
      destination.hash = window.location.hash;
      window.location.replace(destination.href);
      return;
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const languageLink = document.querySelector('.language-link');
    if (!languageLink) return;
    languageLink.addEventListener('click', () => {
      rememberLanguage(languageLink.hreflang);
    });
  });
})();
