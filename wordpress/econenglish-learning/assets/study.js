(function (factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory;
  else factory(document, window);
}(function (document, window) {
  'use strict';
  const key = 'econenglish.completed.v1';
  const lesson = document.querySelector('[data-eel-page="lesson"]');
  const article = lesson && (lesson.closest('article') || lesson.parentElement);
  const controls = lesson && lesson.querySelector('[data-eel-controls]');
  const sections = article ? Array.from(article.querySelectorAll('[data-eel-section]')) : [];
  const complete = controls && controls.querySelector('[data-eel-complete]');

  function read() {
    try {
      const value = JSON.parse(window.localStorage.getItem(key) || '[]');
      return Array.isArray(value) ? value.filter(id => typeof id === 'string' && /^\d+$/.test(id)).slice(0, 200) : [];
    } catch (_) { return []; }
  }

  function updateMarks() {
    const ids = read();
    if (complete) {
      const done = ids.includes(lesson.dataset.eelLesson);
      complete.setAttribute('aria-pressed', String(done));
      complete.textContent = done ? '学習済みを取り消す' : '学習済みにする';
    }
    document.querySelectorAll('.eel-cards [data-eel-target]').forEach(link => {
      const card = link.closest('li');
      if (!card) return;
      let label = card.querySelector('[data-eel-completed-label]');
      if (ids.includes(link.dataset.eelTarget)) {
        if (!label) {
          label = document.createElement('span');
          label.dataset.eelCompletedLabel = '';
          label.className = 'eel-completed-label';
          label.textContent = '学習済み';
          card.append(label);
        }
      } else if (label) label.remove();
    });
  }

  function signal(name, data) {
    document.dispatchEvent(new window.CustomEvent('eel:learning', {detail: Object.assign({name}, data)}));
  }

  function mode(value) {
    sections.forEach(section => {
      section.hidden = value === 'listening' && !['audio', 'listening'].includes(section.dataset.eelSection);
    });
    if (value === 'listening') {
      const questions = article.querySelector('[data-eel-section="listening"]');
      if (questions) questions.querySelectorAll('details').forEach(detail => { detail.open = false; });
    }
    controls.querySelectorAll('[data-eel-mode]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.eelMode === value)));
    controls.querySelector('[data-eel-mode-status]').textContent = value === 'listening'
      ? '英文と解説を隠しています。音声を聞いてクイズに答えたら、「英文を確認」または「全文を表示」を選んでください。'
      : 'すべての英文と解説を表示しています。';
    signal('lesson_mode_change', {mode: value});
  }

  if (controls) {
    controls.hidden = false;
    const supported = ['audio', 'script', 'listening'].every(type => sections.some(s => s.dataset.eelSection === type));
    if (supported) {
      controls.querySelectorAll('[data-eel-mode]').forEach(button => button.addEventListener('click', () => mode(button.dataset.eelMode)));
      // Capture before theme/TOC smooth-scroll handlers can stop propagation.
      document.addEventListener('click', event => {
        const link = event.target.closest('a[href]');
        if (!link) return;
        try {
          const url = new window.URL(link.href, window.location.href);
          if (url.origin !== window.location.origin || url.pathname !== window.location.pathname || !url.hash) return;
          const target = document.getElementById(decodeURIComponent(url.hash.slice(1)));
          if (link.hasAttribute('data-eel-reveal') || (target && target.closest('[data-eel-section][hidden]'))) mode('full');
        } catch (_) { /* A malformed third-party fragment should not affect navigation. */ }
      }, true);
    } else {
      controls.querySelector('.eel-mode-buttons').hidden = true;
      controls.querySelector('nav').hidden = true;
      controls.querySelector('[data-eel-mode-status]').textContent = 'この教材では全文を表示しています。';
    }
    complete.addEventListener('click', () => {
      const id = lesson.dataset.eelLesson;
      const ids = read();
      const done = ids.includes(id);
      const updated = done ? ids.filter(item => item !== id) : [id, ...ids].slice(0, 200);
      try {
        window.localStorage.setItem(key, JSON.stringify(updated));
        controls.querySelector('[data-eel-storage-status]').textContent = done ? '学習済みの印を取り消しました。' : 'このブラウザに学習済みの印を保存しました。';
        updateMarks();
        signal('lesson_mark_complete', {action: done ? 'cleared' : 'marked'});
      } catch (_) {
        controls.querySelector('[data-eel-storage-status]').textContent = 'このブラウザでは学習済みの印を保存できません。保存を許可する設定か確認してください。';
      }
    });
  }
  updateMarks();
  window.addEventListener('storage', event => { if (event.key === key || event.key === null) updateMarks(); });
}));
