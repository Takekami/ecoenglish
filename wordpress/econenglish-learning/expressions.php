<?php
if (!defined('ABSPATH')) { exit; }

/** Reviewed expressions; only display when the exact quote still exists in Script. */
final class Econenglish_Expressions {
    public static function for_post($post) {
        $items = array(
            1931 => array(
                'term' => 'enter merger discussions', 'meaning' => '合併協議に入る',
                'quote' => 'In northern Japan, several banks have announced plans to enter merger discussions.',
                'translation' => '北日本の複数の銀行が、合併協議に入る計画を発表しました。',
                'audio' => 'assets/expressions/1931-sentence.mp3',
                'extension_term' => 'hold merger talks', 'extension_meaning' => '合併協議を行う',
                'extension_note' => 'enter は協議に入ること、hold は協議を行うことを表します。',
                'reference_url' => 'https://view.news.eu.nasdaq.com/view?id=b07a4285b2da297d8eac65d56eeb9b48e&lang=en&src=micro',
                'reference_title' => 'Arion Bankの公式発表（Nasdaq掲載）',
                'checked_on' => '2026-10-29',
            ),
        );
        if (!$post || !isset($items[$post->ID])) { return null; }
        $item = $items[$post->ID];
        $script = '';
        foreach (Econenglish_Growth::sections($post->post_content) as $part) {
            if ($part['type'] === 'script') { $script = html_entity_decode(wp_strip_all_tags($part['html']), ENT_QUOTES | ENT_HTML5, 'UTF-8'); break; }
        }
        // No guessed sentence if a source lesson is edited after review.
        if (strpos($script, $item['quote']) === false) { return null; }
        return $item;
    }

    public static function render($item) {
        if (!$item) { return ''; }
        $quote = str_replace(esc_html($item['term']), '<mark>' . esc_html($item['term']) . '</mark>', esc_html($item['quote']));
        return '<section class="eel eel-lesson-section eel-expressions" id="eel-expressions" data-eel-section="expressions" aria-labelledby="eel-expressions-heading">'
            . '<h2 id="eel-expressions-heading">この回の使える表現</h2>'
            . '<p class="eel-expression-term" lang="en">' . esc_html($item['term']) . '</p>'
            . '<p><strong>' . esc_html($item['meaning']) . '</strong> ― この意味を表す言い方の一つです。</p>'
            . '<p>Podcast本文では、次の一文に出てきます。</p>'
            . '<blockquote lang="en">' . $quote . '</blockquote>'
            . '<p>' . esc_html($item['translation']) . '</p>'
            . '<div class="eel-sentence-player"><label for="eel-expression-audio">この一文を聞く</label>'
            . '<audio id="eel-expression-audio" controls preload="none" data-eel-expression-audio="sentence" src="'
            . esc_url(set_url_scheme(plugins_url($item['audio'], __FILE__), 'https')) . '"></audio>'
            . '<button type="button" data-eel-repeat aria-pressed="false" aria-controls="eel-expression-audio" hidden>繰り返し：オフ</button>'
            . '<p class="eel-note">本文の一文をそのまま読み上げた学習用の合成音声です。ニュースは教材公開時点の内容です。</p></div>'
            . '<details class="eel-expression-extension"><summary>応用：関連する言い方を見る</summary>'
            . '<p><strong lang="en">' . esc_html($item['extension_term']) . '</strong> ― ' . esc_html($item['extension_meaning']) . '</p>'
            . '<p>' . esc_html($item['extension_note']) . '</p></details>'
            . '<details><summary>用例の確認元</summary><p><a href="' . esc_url($item['reference_url']) . '" rel="noopener noreferrer" target="_blank">'
            . esc_html($item['reference_title']) . '</a>（確認日：' . esc_html($item['checked_on']) . '）</p>'
            . '<p>実際の用例を確認した記録です。唯一の言い方や使用頻度の順位を示すものではありません。</p></details>'
            . '<nav class="eel-lesson-actions" aria-label="表現から学習を続ける"><a href="#eel-script" data-eel-reveal>全文で確認する</a>'
            . '<a href="#eel-audio">この回の音声を聞く</a><a href="#eel-listening">クイズに進む</a>'
            . '<a href="#eel-start">学習メニューに戻る</a></nav></section>';
    }
}
