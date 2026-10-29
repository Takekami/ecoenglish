<?php
if (!defined('ABSPATH')) { exit; }
require_once __DIR__ . '/learning-content.php';

final class Econenglish_Growth {
    public static function init() {
        add_shortcode('econenglish_article', array(__CLASS__, 'article'));
        add_shortcode('econenglish_weekly', array(__CLASS__, 'weekly'));
    }

    public static function setup() {
        foreach (eel_learning_articles() as $key => $article) {
            self::ensure_page($key, $article['slug'], $article['title'], $article['excerpt'],
                '[econenglish_article key="' . $key . '"]');
        }
        self::ensure_page('weekly', 'weekly-review', '今週の英語ニュース復習｜3本で振り返る',
            '毎週月曜更新。前週公開の英語ニュース教材から最大3本を選び、元教材のリスニング問題と解答を使って復習できます。', '[econenglish_weekly]');
        self::schedule();
        self::clear_cache();
    }

    private static function ensure_page($key, $slug, $title, $excerpt, $content) {
        $page = get_page_by_path($slug);
        if ($page) {
            // Never overwrite unrelated content that happens to occupy a slug.
            if ($page->post_status === 'publish' && strpos($page->post_content, $content) !== false) {
                update_option('econ_' . $key . '_id', $page->ID, false);
            }
            return;
        }
        $id = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
            'post_name' => $slug, 'post_title' => $title, 'post_excerpt' => $excerpt,
            'post_content' => $content, 'comment_status' => 'closed'), true);
        if (!is_wp_error($id)) { update_option('econ_' . $key . '_id', $id, false); }
    }

    public static function clear_cache() {
        if (function_exists('wpfc_clear_all_cache')) { wpfc_clear_all_cache(); }
    }

    public static function schedule() {
        if (!wp_next_scheduled('econ_weekly_refresh')) {
            $now = current_datetime();
            $next = $now->modify('next monday')->setTime(6, 0);
            wp_schedule_single_event($next->getTimestamp(), 'econ_weekly_refresh');
        }
    }

    public static function refresh() {
        self::clear_cache();
        self::schedule();
    }

    public static function no_cache_weekly() {
        $id = (int) get_option('econ_weekly_id');
        if ($id && is_page($id)) {
            if (!defined('DONOTCACHEPAGE')) { define('DONOTCACHEPAGE', true); }
            nocache_headers();
        }
    }

    public static function help_links() {
        $html = '<ul class="eel-help-links">';
        foreach (eel_learning_articles() as $key => $article) {
            $html .= '<li>' . Econenglish_Learning::link(Econenglish_Learning::page_url($key), $article['title'], 'learning_guide_click') . '</li>';
        }
        return $html . '</ul>';
    }

    public static function article($atts) {
        $atts = shortcode_atts(array('key' => ''), $atts);
        $articles = eel_learning_articles();
        if (!isset($articles[$atts['key']])) { return ''; }
        $item = $articles[$atts['key']];
        $args = array('posts_per_page' => 3, 'no_found_rows' => true);
        if ($item['topic']) { $args['tax_query'] = array(array('taxonomy' => Econenglish_Learning::TAX,
            'field' => 'slug', 'terms' => $item['topic'])); }
        return '<div class="eel" data-eel-page="learning-guide">' . Econenglish_Learning::nav()
            . $item['html'] . '<h2>教材で試してみる</h2>'
            . Econenglish_Learning::cards(Econenglish_Learning::lesson_query($args)->posts, 'guide_lesson_click')
            . '<h2>ほかの学習ガイド</h2>' . self::help_links() . '</div>';
    }

    /** Preserve stored content, but remove document wrappers from old generated posts. */
    public static function clean_fragment($html) {
        $html = preg_replace('~<head\b[^>]*>.*?</head>~is', '', $html);
        return preg_replace('~<!DOCTYPE[^>]*>|</?(?:html|body)\b[^>]*>~i', '', $html);
    }

    public static function section_type($heading) {
        $text = wp_strip_all_tags($heading);
        $names = array('audio' => 'Audio|音声', 'script' => 'Script|スクリプト',
            'vocabulary' => 'Vocabulary|単語', 'grammar' => 'Grammar|文法',
            'listening' => 'Listening Questions|リスニングクイズ|リスニング問題',
            'reading' => 'Reading Questions|読解クイズ|リーディング問題',
            'insight' => '日本語での経済|Economic Insight', 'practice' => '自分の考え|Practice');
        foreach ($names as $type => $pattern) {
            if (preg_match('/' . $pattern . '/iu', $text)) { return $type; }
        }
        return '';
    }

    public static function sections($content) {
        $pieces = preg_split('~(?=<h2\b)~i', self::clean_fragment($content));
        $result = array();
        foreach ($pieces as $part) {
            $type = preg_match('~^<h2\b[^>]*>.*?</h2>~is', $part, $m) ? self::section_type($m[0]) : '';
            $result[] = array('type' => $type, 'html' => $part);
        }
        return $result;
    }

    public static function study_content($content) {
        $html = '';
        $used = array();
        foreach (self::sections($content) as $part) {
            $type = $part['type'];
            if (!$type || isset($used[$type])) { $html .= $part['html']; continue; }
            $used[$type] = true;
            $html .= '<section class="eel-lesson-section" id="eel-' . esc_attr($type)
                . '" data-eel-section="' . esc_attr($type) . '">' . $part['html'] . '</section>';
        }
        return $html;
    }

    public static function controls() {
        return '<div class="eel-study" data-eel-controls hidden>'
            . '<p><strong>聞く → 解く → 英文を確認</strong></p>'
            . '<div class="eel-mode-buttons" role="group" aria-label="教材の表示モード">'
            . '<button type="button" data-eel-mode="listening" aria-pressed="false">聞く・解くモード</button>'
            . '<button type="button" data-eel-mode="full" aria-pressed="true">全文を表示</button></div>'
            . '<p class="eel-study-status" aria-live="polite" data-eel-mode-status>音声とクイズを先に使いたいときは、聞く・解くモードを選べます。</p>'
            . '<nav aria-label="学習ステップ"><a href="#eel-audio">1. 音声</a> '
            . '<a href="#eel-listening">2. クイズ</a> <a href="#eel-script" data-eel-reveal>3. 英文を確認</a></nav>'
            . '<button type="button" data-eel-complete aria-pressed="false">学習済みにする</button>'
            . '<p class="eel-note">学習済みの印はこのブラウザだけに保存されます。別端末とは同期せず、正答率や習熟度の判定ではありません。</p>'
            . '<p role="status" data-eel-storage-status></p></div>';
    }

    /** Copy one existing true/false question and its existing answer, without generating facts. */
    public static function quiz($content) {
        if (!class_exists('DOMDocument')) { return null; }
        foreach (self::sections($content) as $part) {
            if ($part['type'] !== 'listening') { continue; }
            $dom = new DOMDocument();
            $previous = libxml_use_internal_errors(true);
            $loaded = $dom->loadHTML('<?xml encoding="UTF-8">' . $part['html']);
            libxml_clear_errors();
            libxml_use_internal_errors($previous);
            if (!$loaded) { return null; }
            $xpath = new DOMXPath($dom);
            $questions = $xpath->query('//li[not(ancestor::details)]');
            $answers = $xpath->query('//details//li');
            if (!$questions->length || !$answers->length) { return null; }
            $question = trim(preg_replace('/\s+/u', ' ', $questions->item(0)->textContent));
            $answer = trim(preg_replace('/^\s*1[.．)]\s*/u', '', $answers->item(0)->textContent));
            if (!preg_match('/^(?:1[.．)]\s*)?True\s*\/\s*False\s*:/iu', $question)
                || !preg_match('/^(True|False)\b/i', $answer)) { return null; }
            return array('question' => $question, 'answer' => $answer);
        }
        return null;
    }

    public static function week_bounds($now = null) {
        $now = $now ?: current_datetime();
        $monday = $now->setTime(0, 0)->modify('-' . ((int) $now->format('N') - 1) . ' days');
        return array($monday->modify('-7 days'), $monday);
    }

    public static function weekly() {
        list($start, $end) = self::week_bounds();
        $query = Econenglish_Learning::lesson_query(array('posts_per_page' => 30, 'no_found_rows' => true,
            'date_query' => array(array('after' => $start->format('Y-m-d H:i:s'),
                'before' => $end->modify('-1 second')->format('Y-m-d H:i:s'), 'inclusive' => true))));
        $items = array();
        foreach ($query->posts as $post) {
            if (!Econenglish_Learning::is_lesson($post)) { continue; }
            $quiz = self::quiz($post->post_content);
            if ($quiz) { $items[] = array('post' => $post, 'quiz' => $quiz); }
            if (count($items) === 3) { break; }
        }
        $html = '<div class="eel" data-eel-page="weekly"><p class="eel-kicker">WEEKLY REVIEW / 毎週月曜日更新</p>'
            . '<p class="eel-lead">3本で、英語ニュースを振り返る。</p>'
            . '<p>対象：' . esc_html($start->format('Y/m/d') . '〜' . $end->modify('-1 day')->format('m/d'))
            . 'に公開した教材。前週の教材から最大3本を選び、元教材の問題と解答で復習します。</p>'
            . Econenglish_Learning::nav()
            . '<p class="eel-note">ニュースは元教材の公開時点の内容です。この復習は元教材の抜粋であり、新しいニュース解説ではありません。</p>';
        if (!$items) {
            $html .= '<p>対象期間に、復習問題を取り出せる教材はありませんでした。教材一覧から好きな1本を選んで復習してみましょう。</p>';
        }
        foreach ($items as $index => $item) {
            $post = $item['post'];
            $html .= '<section class="eel-weekly-item"><h2>' . ($index + 1) . '. ' . esc_html(get_the_title($post)) . '</h2>'
                . '<p>まず元教材の音声を聞いてから、この問題に答えてみましょう。</p>'
                . Econenglish_Learning::link(set_url_scheme(get_permalink($post), 'https'), '音声と元の教材を開く', 'weekly_lesson_click', 'data-eel-target="' . (int) $post->ID . '"')
                . '<p class="eel-weekly-question">' . esc_html($item['quiz']['question']) . '</p>'
                . '<details data-eel-weekly-answer><summary>答えを見る</summary><p>' . esc_html($item['quiz']['answer']) . '</p>'
                . '<p>答えの根拠は元教材の英文で確認してください。</p></details></section>';
        }
        return $html . '<h2>次の学習へ</h2>' . self::help_links() . '</div>';
    }

    public static function admin_setup() {
        if (!current_user_can('manage_options')) { wp_die('権限がありません'); }
        check_admin_referer('econ_growth_setup');
        self::setup();
        wp_safe_redirect(admin_url('tools.php?page=econenglish-learning'));
        exit;
    }
}
add_action('init', array('Econenglish_Growth', 'init'));
add_action('template_redirect', array('Econenglish_Growth', 'no_cache_weekly'));
add_action('econ_weekly_refresh', array('Econenglish_Growth', 'refresh'));
add_action('admin_post_econ_growth_setup', array('Econenglish_Growth', 'admin_setup'));
