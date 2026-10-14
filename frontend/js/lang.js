/**
 * ChildNutri AI — Language Toggle Engine
 * Switches all user-visible text between English and Hindi on the client.
 * Persists selection via localStorage key: 'childnutri_lang'
 */

// Default language stored in localStorage or English
let currentLang = localStorage.getItem('childnutri_lang') || 'en';

// Apply translations to every element with data-i18n attribute
function applyTranslations(lang) {
  const allTranslations = window.TRANSLATIONS || (typeof TRANSLATIONS !== 'undefined' ? TRANSLATIONS : null);
  if (!allTranslations || !allTranslations[lang]) {
    console.warn(`[i18n] Translations not available for language: ${lang}`);
    return;
  }
  currentLang = lang;
  localStorage.setItem('childnutri_lang', lang);

  const dict = allTranslations[lang];

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const translation = dict[key];
    if (translation !== undefined) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = translation;
      } else {
        // If element has a child badge or icon with class 'step-num', preserve it
        const stepNum = el.querySelector('.step-num');
        const badgeDot = el.querySelector('.badge-dot');
        if (stepNum) {
          el.innerHTML = `<span class="step-num">${stepNum.textContent}</span>${translation}`;
        } else if (badgeDot) {
          el.innerHTML = `<span class="badge-dot"></span>${translation}`;
        } else {
          el.textContent = translation;
        }
      }
    }
  });

  // Update toggle button text (shows the other language available to switch to)
  const btn = document.getElementById('lang-toggle');
  if (btn) {
    btn.textContent = lang === 'en' ? 'हिंदी' : 'English';
    btn.setAttribute('title', lang === 'en' ? 'हिंदी में बदलें' : 'Switch to English');
  }

  // Update HTML document lang attribute
  document.documentElement.lang = lang === 'hi' ? 'hi' : 'en';

  // Dispatch custom event for pages that need to re-render dynamic content (e.g. results or review)
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}

function toggleLanguage() {
  applyTranslations(currentLang === 'en' ? 'hi' : 'en');
}

// Auto-apply on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    applyTranslations(currentLang);
  });
} else {
  applyTranslations(currentLang);
}
