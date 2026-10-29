<?php
/**
 * Plugin Name: Econenglish Learning
 * Description: 学習ガイド、テーマ別教材一覧、次の教材と学習行動の計測。
 * Version: 1.2.0
 * Requires at least: 6.4
 * Requires PHP: 7.4
 * Author: Econenglish
 */
if (!defined('ABSPATH')) { exit; }
require_once __DIR__ . '/growth.php';
require_once __DIR__ . '/expressions.php';

final class Econenglish_Learning {
    const VERSION = '1.2.0';
    const TAX = 'econ_topic';

    public static function topics() {
        return array(
            'prices' => array('物価・暮らし', '物価、賃金、消費など、身近な経済の英語を学びます。', 'inflation|deflation|prices?|wages?|salar(?:y|ies)|cost of living|consumers?|households?|housing|food security|物価|インフレ|賃金|消費|食料'),
            'finance' => array('金利・為替・市場', '金利、通貨、株式市場のニュースで使う表現を学びます。', 'interest rates?|central banks?|federal reserve|bank of japan|currenc(?:y|ies)|yuan|yen|dollar|stocks?|shares?|bonds?|markets?|gold|金利|為替|中央銀行|円安|株価|金融'),
            'business' => array('企業・テクノロジー', '企業の動き、AI、仕事に関するニュースを読み解きます。', 'compan(?:y|ies)|business|firms?|billionaire|acqui(?:re|sition)|merger|royal mail|tech(?:nology)?|artificial intelligence|AI|OpenAI|Apple|Musk|Micron|Microsoft|Google|Amazon|Alibaba|Toyota|NTT|Samsung|TSMC|Tesla|Dreame|robots?|smartphones?|electric cars?|innovations?|medical|chips?|semiconductors?|data cent(?:er|re)|cyberattacks?|企業|買収|半導体|人工知能|サイバー'),
            'trade' => array('貿易・世界経済', '輸出入、関税、経済成長を英語で理解します。', 'trade|tariffs?|exports?|imports?|GDP|growth|IMF|econom(?:y|ies|ic)|貿易|関税|輸出|輸入|成長|世界経済'),
            'energy' => array('環境・エネルギー', 'エネルギーや気候変動と経済のつながりを学びます。', 'energy|oil|natural gas|LNG|wind farms?|climate|carbon|wildfires?|renewable|emissions?|環境|エネルギー|石油|気候|炭素|山火事'),
            'society' => array('社会・国際情勢', '政策や国際情勢を伝えるニュースの英語に触れます。', 'policy|government|election|protests?|president|minister|war|military|security|raids?|snipers?|tear gas|政治|政策|政府|選挙|抗議|国際情勢'),
        );
    }

    public static function init() {
        register_taxonomy(self::TAX, 'post', array(
            'label' => '教材テーマ', 'public' => false, 'show_ui' => true,
            'show_in_rest' => true, 'hierarchical' => false, 'rewrite' => false,
        ));
        add_shortcode('econenglish_library', array(__CLASS__, 'library'));
        add_shortcode('econenglish_guide', array(__CLASS__, 'guide'));
    }

    public static function is_lesson($post) {
        return $post && $post->post_type === 'post' && $post->post_status === 'publish'
            && preg_match('/<audio\b|<iframe[^>]+spreaker\.com/i', $post->post_content)
            && preg_match('/Script|スクリプト/iu', $post->post_content);
    }

    // Match whole English words; prefer the headline over incidental script vocabulary.
    public static function classify($title, $content) {
        $script = '';
        if (preg_match('/<h[23][^>]*>[^<]*(?:Script|スクリプト)[^<]*<\/h[23]>(.*?)(?:<h[23]|$)/isu', $content, $m)) {
            $script = wp_strip_all_tags($m[1]);
        }
        $scores = array();
        foreach (self::topics() as $slug => $topic) {
            $pattern = '/(?<![a-z])(?:' . $topic[2] . ')(?![a-z])/iu';
            $scores[$slug] = 5 * preg_match_all($pattern, $title) + min(4, preg_match_all($pattern, $script));
        }
        arsort($scores);
        $best = (int) reset($scores);
        if (!$best) { return array('society'); }
        $chosen = array();
        foreach ($scores as $slug => $score) {
            if ($score >= max(5, $best / 2)) { $chosen[] = $slug; }
            if (count($chosen) === 2) { break; }
        }
        return $chosen ?: array(array_key_first($scores));
    }

    public static function index_post($id, $post) {
        if (wp_is_post_revision($id) || wp_is_post_autosave($id)) { return; }
        if (!self::is_lesson($post)) {
            if ($post->post_type === 'post') { delete_post_meta($id, '_econ_lesson'); }
            return;
        }
        update_post_meta($id, '_econ_lesson', '1');
        // Editors can opt out of automatic topic assignment for a manually curated lesson.
        if (!get_post_meta($id, '_econ_manual_topics', true)) {
            wp_set_object_terms($id, self::classify($post->post_title, $post->post_content), self::TAX);
        }
    }

    public static function activate() {
        self::init();
        foreach (self::topics() as $slug => $topic) {
            if (!term_exists($slug, self::TAX)) { wp_insert_term($topic[0], self::TAX, array('slug' => $slug)); }
        }
        $library = get_page_by_path('lesson-library');
        if (!$library) {
            $id = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
                'post_name' => 'lesson-library', 'post_title' => 'テーマ別の英語ニュース教材',
                'post_excerpt' => '物価、金利、企業、貿易、環境、国際情勢から選べる中級者向け英語ニュース教材。音声・スクリプト・単語・理解度クイズで学習できます。',
                'post_content' => '[econenglish_library]', 'comment_status' => 'closed'), true);
            if (!is_wp_error($id)) { update_option('econ_library_id', $id, false); }
        } elseif (has_shortcode($library->post_content, 'econenglish_library')) {
            update_option('econ_library_id', $library->ID, false);
        }
        $guide = get_page_by_path('howtousethisblogandpodcast', OBJECT, array('post', 'page'));
        if ($guide && $guide->post_status === 'publish') {
            update_option('econ_guide_id', $guide->ID, false);
        } else {
            $guide = get_page_by_path('start-here');
            if (!$guide) {
                $id = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
                    'post_name' => 'start-here', 'post_title' => '初めての方へ｜英語ニュース教材の使い方',
                    'post_content' => '[econenglish_guide]', 'comment_status' => 'closed'), true);
                if (!is_wp_error($id)) { update_option('econ_guide_id', $id, false); }
            } elseif (has_shortcode($guide->post_content, 'econenglish_guide')) {
                update_option('econ_guide_id', $guide->ID, false);
            }
        }
        // Snapshot IDs once, so new publications do not shift an offset during backfill.
        if (false === get_option('econ_index_queue', false)) {
            update_option('econ_index_queue', get_posts(array('post_type' => 'post', 'post_status' => 'publish',
                'numberposts' => -1, 'fields' => 'ids', 'orderby' => 'ID', 'order' => 'ASC')), false);
        }
        self::index_batch();
        Econenglish_Growth::setup();
    }

    public static function index_batch() {
        $queue = get_option('econ_index_queue', array());
        foreach (array_splice($queue, 0, 60) as $id) {
            $post = get_post($id);
            if ($post) { self::index_post($id, $post); }
        }
        update_option('econ_index_queue', $queue, false);
        if ($queue && !wp_next_scheduled('econ_index_batch')) { wp_schedule_single_event(time() + 10, 'econ_index_batch'); }
        if (function_exists('wpfc_clear_all_cache')) { wpfc_clear_all_cache(); }
    }

    public static function page_url($kind) {
        $id = (int) get_option('econ_' . $kind . '_id');
        return $id && get_post_status($id) === 'publish' ? set_url_scheme(get_permalink($id), 'https') : '';
    }

    public static function link($url, $text, $event, $extra = '') {
        if (!$url) { return ''; }
        return '<a class="eel-link" href="' . esc_url($url) . '" data-eel-event="' . esc_attr($event) . '" ' . $extra . '>' . esc_html($text) . '</a>';
    }

    public static function nav() {
        return '<nav class="eel-nav" aria-label="教材の学習ナビ">'
            . self::link(self::page_url('guide'), '初めての方へ', 'guide_click')
            . self::link(self::page_url('library'), 'テーマ別に教材を探す', 'library_click')
            . self::link(self::page_url('weekly'), '今週の復習', 'weekly_click') . '</nav>';
    }

    public static function cards($posts, $event = 'lesson_select') {
        $html = '<ul class="eel-cards">';
        foreach ($posts as $post) {
            $terms = get_the_terms($post->ID, self::TAX);
            $labels = $terms && !is_wp_error($terms) ? wp_list_pluck($terms, 'name') : array();
            $title = preg_replace('/^(?:英語ニュース教材[：:]\s*|【Asia Business English】\s*)/u', '', get_the_title($post));
            $title = preg_replace('/（(?:Intermediate\s*レベル|B1[–—-]B2)）$/u', '', $title);
            $html .= '<li><span class="eel-kicker">' . esc_html(implode(' / ', $labels)) . '</span>'
                . self::link(set_url_scheme(get_permalink($post), 'https'), $title, $event, 'data-eel-target="' . (int) $post->ID . '"')
                . '<span class="eel-date">教材公開 ' . esc_html(get_the_date('Y/m/d', $post)) . ' · 音声・スクリプト・クイズ</span></li>';
        }
        return $html . '</ul>';
    }

    public static function lesson_query($args = array()) {
        return new WP_Query(array_merge(array('post_type' => 'post', 'post_status' => 'publish',
            'posts_per_page' => 12, 'ignore_sticky_posts' => true, 'orderby' => array('date' => 'DESC', 'ID' => 'DESC'),
            'meta_key' => '_econ_lesson', 'meta_value' => '1'), $args));
    }

    public static function library() {
        $topics = self::topics();
        $topic = isset($_GET['lesson_topic']) && is_string($_GET['lesson_topic']) ? sanitize_key(wp_unslash($_GET['lesson_topic'])) : '';
        if (!isset($topics[$topic])) { $topic = ''; }
        $page = isset($_GET['lesson_page']) && is_scalar($_GET['lesson_page']) ? min(10000, max(1, absint($_GET['lesson_page']))) : 1;
        $args = array('paged' => $page);
        if ($topic) { $args['tax_query'] = array(array('taxonomy' => self::TAX, 'field' => 'slug', 'terms' => $topic)); }
        $query = self::lesson_query($args);
        $base = self::page_url('library');
        $html = '<div class="eel" data-eel-page="library"><p class="eel-kicker">ECONENGLISH / LESSON LIBRARY</p>'
            . '<p class="eel-lead">気になる話題から、英語を学ぼう。</p><p>音声を聞き、スクリプトで確かめ、クイズで復習。中級者向けのニュース教材をテーマから選べます。</p>'
            . self::nav() . '<nav class="eel-topics" aria-label="教材テーマ">'
            . self::link($base, 'すべて', 'topic_select', !$topic ? 'aria-current="page"' : '');
        foreach ($topics as $slug => $item) {
            $html .= self::link(add_query_arg('lesson_topic', $slug, $base), $item[0], 'topic_select', 'data-eel-topic="' . esc_attr($slug) . '"' . ($topic === $slug ? ' aria-current="page"' : ''));
        }
        $html .= '</nav><h2>' . esc_html($topic ? $topics[$topic][0] : 'すべての教材') . '</h2>';
        if ($topic) { $html .= '<p>' . esc_html($topics[$topic][1]) . '</p>'; }
        $html .= '<p class="eel-note">掲載ニュースは各教材の公開時点の内容です。現在の状況とは異なる場合があります。</p>';
        $html .= $query->posts ? self::cards($query->posts) : '<p>このテーマの教材は準備中です。別のテーマを選んでください。</p>';
        $html .= '<nav class="eel-pagination" aria-label="教材一覧のページ送り">';
        $filtered = $topic ? add_query_arg('lesson_topic', $topic, $base) : $base;
        if ($page > 1) { $html .= self::link(add_query_arg('lesson_page', $page - 1, $filtered), '前の教材へ', 'library_page'); }
        if ($page < $query->max_num_pages) { $html .= self::link(add_query_arg('lesson_page', $page + 1, $filtered), '次の教材へ', 'library_page'); }
        return $html . '</nav></div>';
    }

    public static function guide() {
        // Royal Mail has been individually reviewed; other suggestions are explicitly recent lessons.
        $reviewed = get_post(1469);
        $starter = self::is_lesson($reviewed) ? array($reviewed) : array();
        $recent = self::lesson_query(array('posts_per_page' => 3 - count($starter), 'post__not_in' => wp_list_pluck($starter, 'ID'), 'no_found_rows' => true));
        $html = '<div class="eel" data-eel-page="guide"><p class="eel-kicker">START HERE / 初めての方へ</p>'
            . '<p class="eel-lead">海外ニュースで、<br>聞く・読む・わかる。</p>'
            . '<p>英語の基礎は学んだけれど、海外ニュースをそのまま聞くのは難しい。そんな中級者のための、音声・スクリプト・日本語解説付き教材です。</p>'
            . '<p class="eel-note">レベルの目安はB1〜B2。試験スコアとの対応や成果を保証するものではありません。まず1本試して、聞きやすさを確かめてください。</p>'
            . '<h2>まずは1本、10分から</h2><ol class="eel-steps">'
            . '<li><strong>音声を聞く</strong><p>最初はスクリプトを見ずに。話題と大まかな結論をつかみます。</p></li>'
            . '<li><strong>英文と単語を確かめる</strong><p>聞き取れなかった箇所をスクリプトで確認。覚えたい表現を1つ選びます。</p></li>'
            . '<li><strong>クイズで復習する</strong><p>問題に答えてから解答を開きます。日本語解説で内容を整理し、もう一度聞いてみましょう。</p></li></ol>'
            . '<p>忙しい日は音声だけでも大丈夫。すべてを一度に終える必要はありません。</p>'
            . '<h2>最初に試す教材</h2><p>買収ニュースの教材と、最近公開した教材から選べます。興味のある話題を1本開いてください。</p>'
            . self::cards(array_merge($starter, $recent->posts), 'starter_lesson_click')
            . '<h2>好きな話題から続ける</h2><p>物価、金利、企業、貿易など、気になるテーマの教材をまとめて探せます。</p>'
            . self::link(self::page_url('library'), 'テーマ別の教材一覧を見る', 'library_click')
            . '<h2>この教材について</h2><p>入門教材とネイティブ向けニュースの間をつなぐ学習材料として、海外ニュースをもとに英語教材を制作しています。AIを制作に使用し、内容の検証も行っていますが、誤りが残る可能性があります。</p>'
            . '<p>ニュースは教材公開時点の内容です。気になる情報は各記事末尾の出典も確認してください。誤りに気づいた場合は、お問い合わせからお知らせください。</p>'
            . self::link(home_url('/contact/', 'https'), 'お問い合わせ', 'contact_click')
            . '<h2>学習を続けるヒント</h2>' . Econenglish_Growth::help_links()
            . self::link(self::page_url('weekly'), '今週の復習に取り組む', 'weekly_click');
        return $html . '</div>';
    }

    public static function content($content) {
        if (is_admin() || is_feed() || !is_singular() || !in_the_loop() || !is_main_query()) { return $content; }
        $post = get_post();
        if ((int) get_option('econ_guide_id') === $post->ID) { return self::guide(); }
        if (!self::is_lesson($post)) { return $content; }
        $terms = wp_get_object_terms($post->ID, self::TAX, array('fields' => 'ids'));
        $args = array('posts_per_page' => 3, 'post__not_in' => array($post->ID), 'no_found_rows' => true);
        $related = array();
        if ($terms && !is_wp_error($terms)) {
            $args['tax_query'] = array(array('taxonomy' => self::TAX, 'terms' => $terms));
            $related = self::lesson_query($args)->posts;
        }
        $heading = '同じテーマで、もう1本';
        if (!$related) {
            unset($args['tax_query']);
            $related = self::lesson_query($args)->posts;
            $heading = '次に学ぶ教材';
        }
        $expression = Econenglish_Expressions::for_post($post);
        $intro = '<div class="eel eel-lesson-start" id="eel-start" data-eel-page="lesson" data-eel-lesson="' . (int) $post->ID . '">'
            . '<p class="eel-learning-title"><strong>この回の学習</strong></p><p>使いたいところから始められます。</p>'
            . Econenglish_Growth::lesson_navigation($content, (bool) $expression)
            . '<details class="eel-study-tools"><summary>聞く・解くモード／学習済みの記録</summary>' . Econenglish_Growth::controls() . '</details>'
            . '<details class="eel-other-tools"><summary>教材一覧・学習ガイド</summary>' . self::nav() . '</details>'
            . '<p class="eel-note">ニュースは教材公開時点の内容です。</p></div>';
        $next = '<section class="eel eel-next" aria-label="次に学ぶ教材"><h2>' . esc_html($heading) . '</h2>'
            . self::cards($related, 'related_lesson_click') . self::link(self::page_url('library'), 'ほかのテーマも探す', 'library_click') . '</section>';
        return $intro . Econenglish_Growth::study_content($content, Econenglish_Expressions::render($expression)) . $next;
    }

    public static function assets() {
        if (is_feed() || is_admin()) { return; }
        wp_enqueue_style('econenglish-learning', set_url_scheme(plugins_url('assets/learning.css', __FILE__), 'https'), array(), self::VERSION);
        wp_enqueue_script('econenglish-learning', set_url_scheme(plugins_url('assets/learning.js', __FILE__), 'https'), array(), self::VERSION, true);
        wp_enqueue_script('econenglish-study', set_url_scheme(plugins_url('assets/study.js', __FILE__), 'https'), array('econenglish-learning'), self::VERSION, true);
        wp_add_inline_script('econenglish-learning', 'window.eelConfig=' . wp_json_encode(array('admin' => current_user_can('edit_posts'), 'measurementId' => 'G-EMJ73ZY8ZW')) . ';', 'before');
    }

    public static function home_entry() {
        if (!is_front_page() && !is_home()) { return; }
        echo '<aside class="eel eel-home" aria-label="Econenglishの学習ガイド"><strong>英語ニュース学習を、ここから。</strong>' . self::nav() . '</aside>';
    }

    public static function admin_menu() {
        add_management_page('教材ナビ', '教材ナビ', 'manage_options', 'econenglish-learning', array(__CLASS__, 'admin_page'));
    }

    public static function admin_page() {
        if (!current_user_can('manage_options')) { return; }
        echo '<div class="wrap"><h1>Econenglish 教材ナビ</h1><p>残りの分類対象: ' . count(get_option('econ_index_queue', array())) . '件</p>';
        echo '<p>新しい教材は保存時に自動分類されます。教材テーマは投稿編集画面でも確認できます。</p><p>'
            . self::link(self::page_url('guide'), '学習ガイドを確認', 'admin_preview') . ' / '
            . self::link(self::page_url('library'), '教材一覧を確認', 'admin_preview') . '</p>';
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
        wp_nonce_field('econ_growth_setup');
        echo '<input type="hidden" name="action" value="econ_growth_setup">';
        submit_button('解説3本と週次復習ページを公開・確認');
        echo '</form>';
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
        wp_nonce_field('econ_index');
        echo '<input type="hidden" name="action" value="econ_index">';
        submit_button('次の60件を分類');
        echo '</form><form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
        wp_nonce_field('econ_index');
        echo '<input type="hidden" name="action" value="econ_index"><input type="hidden" name="restart" value="1">';
        submit_button('全教材を再分類', 'secondary');
        echo '</form><p>プラグインを停止すると追加ナビ・計測とガイドの表示差し替えが停止します。元のガイド本文は変更していません。</p></div>';
    }

    public static function admin_index() {
        if (!current_user_can('manage_options')) { wp_die('権限がありません'); }
        check_admin_referer('econ_index');
        if (isset($_POST['restart']) && $_POST['restart'] === '1') {
            update_option('econ_index_queue', get_posts(array('post_type' => 'post', 'post_status' => 'publish',
                'numberposts' => -1, 'fields' => 'ids', 'orderby' => 'ID', 'order' => 'ASC')), false);
        }
        self::index_batch();
        wp_safe_redirect(admin_url('tools.php?page=econenglish-learning'));
        exit;
    }
}
add_action('init', array('Econenglish_Learning', 'init'));
add_action('save_post_post', array('Econenglish_Learning', 'index_post'), 20, 2);
add_action('econ_index_batch', array('Econenglish_Learning', 'index_batch'));
add_action('wp_enqueue_scripts', array('Econenglish_Learning', 'assets'));
add_action('wp_footer', array('Econenglish_Learning', 'home_entry'));
add_filter('the_content', array('Econenglish_Learning', 'content'), 20);
add_action('admin_menu', array('Econenglish_Learning', 'admin_menu'));
add_action('admin_post_econ_index', array('Econenglish_Learning', 'admin_index'));
register_activation_hook(__FILE__, array('Econenglish_Learning', 'activate'));
register_deactivation_hook(__FILE__, function () {
    wp_clear_scheduled_hook('econ_index_batch');
    wp_clear_scheduled_hook('econ_weekly_refresh');
});
