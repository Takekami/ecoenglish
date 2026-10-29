const test = require('node:test');
const assert = require('node:assert/strict');
const {JSDOM} = require('jsdom');
const setup = require('../econenglish-learning/assets/study.js');

function page() {
  const dom = new JSDOM(`<article>
    <div data-eel-page="lesson" data-eel-lesson="42"><div data-eel-controls hidden>
      <div class="eel-mode-buttons"><button data-eel-mode="listening">聞く・解く</button><button data-eel-mode="full">全文</button></div>
      <p data-eel-mode-status></p><nav><a href="#eel-script" data-eel-reveal>英文を確認</a></nav>
      <button data-eel-complete aria-pressed="false"></button><p data-eel-storage-status></p></div></div>
    <section data-eel-section="audio" id="eel-audio"><audio></audio></section>
    <section data-eel-section="script" id="eel-script"><h2 id="old-toc">Script</h2>Original script</section>
    <section data-eel-section="listening" id="eel-listening"><details open><summary>Answer</summary>True</details></section>
    <section data-eel-section="reading">Reading</section><section data-eel-section="insight">Japanese insight</section>
    <a href="#old-toc" id="toc">Original TOC</a>
    <ul class="eel-cards"><li><a data-eel-target="42">This lesson</a></li></ul></article>`, {url:'https://econenglish.jp/lesson/'});
  const events=[];
  dom.window.document.addEventListener('eel:learning', e => events.push(e.detail));
  setup(dom.window.document, dom.window);
  return {dom, d:dom.window.document, events};
}

test('listening mode hides spoilers, keeps audio/questions, and closes previously opened answers', () => {
  const {d}=page();
  d.querySelector('[data-eel-mode=listening]').click();
  assert.equal(d.querySelector('[data-eel-section=script]').hidden,true);
  assert.equal(d.querySelector('[data-eel-section=insight]').hidden,true);
  assert.equal(d.querySelector('[data-eel-section=audio]').hidden,false);
  assert.equal(d.querySelector('[data-eel-section=listening]').hidden,false);
  assert.equal(d.querySelector('details').open,false);
  assert.equal(d.querySelector('[data-eel-mode=listening]').getAttribute('aria-pressed'),'true');
  d.querySelector('[data-eel-mode=full]').click();
  assert.ok([...d.querySelectorAll('[data-eel-section]')].every(s=>!s.hidden));
  assert.match(d.querySelector('[data-eel-section=script]').textContent,/Original script/);
});
test('both original table-of-contents links and reveal action restore hidden content', () => {
  const {d}=page();
  for(const selector of ['#toc','[data-eel-reveal]']) {
    d.querySelector('[data-eel-mode=listening]').click();
    d.querySelector(selector).click();
    assert.equal(d.querySelector('[data-eel-section=script]').hidden,false);
  }
});
test('completion persists locally, displays on cards, and can be undone', () => {
  const {d,dom,events}=page();
  d.querySelector('[data-eel-complete]').click();
  assert.deepEqual(JSON.parse(dom.window.localStorage.getItem('econenglish.completed.v1')),['42']);
  assert.equal(d.querySelector('[data-eel-completed-label]').textContent,'学習済み');
  assert.equal(events.at(-1).name,'lesson_mark_complete');
  d.querySelector('[data-eel-complete]').click();
  assert.equal(d.querySelector('[data-eel-completed-label]'),null);
  assert.equal(events.at(-1).action,'cleared');
});
test('blocked storage explains failure without breaking study mode', () => {
  const {d,dom}=page();
  Object.defineProperty(dom.window,'localStorage',{get(){throw new Error('blocked');}});
  d.querySelector('[data-eel-complete]').click();
  assert.match(d.querySelector('[data-eel-storage-status]').textContent,/保存できません/);
  d.querySelector('[data-eel-mode=listening]').click();
  assert.equal(d.querySelector('[data-eel-section=script]').hidden,true);
});
test('missing sections retain full content and completion instead of exposing broken mode links', () => {
  const dom=new JSDOM('<article><div data-eel-page="lesson" data-eel-lesson="1"><div data-eel-controls hidden><div class="eel-mode-buttons"></div><nav></nav><p data-eel-mode-status></p><button data-eel-complete></button><p data-eel-storage-status></p></div></div><p>Original</p></article>',{url:'https://econenglish.jp/'});
  setup(dom.window.document,dom.window);
  assert.equal(dom.window.document.querySelector('.eel-mode-buttons').hidden,true);
  assert.match(dom.window.document.body.textContent,/Original/);
});
