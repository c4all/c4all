(function () {
    // Localize jQuery variable
    var jQuery, $;

    var scripts = document.getElementsByTagName('script');
    var C4ALL_SERVER = 'http://c4all.devsrv.net';
    var THREAD;
    var COMMENTS_ENABLED = true;
    var IP_ADDRESS = '';
    var SPELLCHECK_ENABLED = false;
    var MIN_PARENT_WIDTH = 600;
    var SPELLCHECK_LOCALIZATION;
    var spellchecker;
    var READSPEAKER_BASE_URL = 'http://app.eu.readspeaker.com/cgi-bin/rsent?';

    // try to get c4all domain from the script tag
    for (var i in scripts) {
        if (scripts[i].src && scripts[i].src.match('/static/js/comments.js')) {
            C4ALL_SERVER = 'http://' + scripts[i].src.match(/\/\/([a-zA-Z0-9\-_\.\:]+)\//).pop();
        }
    }

    var THREAD_URL = window.location.pathname;
    var DOMAIN = window.location.host;
    var TITLE_SELECTOR = '#c4all-admin-page-title';

    function loadJquery() {
        if (window.jQuery === undefined || window.jQuery.fn.jquery !== '1.11.0') {
            var script_tag = document.createElement('script');
            script_tag.setAttribute('type', 'text/javascript');
            script_tag.setAttribute('src',
                'http://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js');
            if (script_tag.readyState) {
                script_tag.onreadystatechange = function () { // For old versions of IE
                    if (this.readyState === 'complete' || this.readyState === 'loaded') {
                        jqueryLoadHandler();
                    }
                };
            } else { // Other browsers
                script_tag.onload = jqueryLoadHandler;
            }
            // Try to find the head, otherwise default to the documentElement
            (document.getElementsByTagName('head')[0] || document.documentElement).appendChild(script_tag);
        } else {
            // The jQuery version on the window is the one we want to use
            $ = jQuery = window.jQuery;
            window.jQuery_c4all = $;
            main();
        }
    }

    function myIP() {
        var url = 'http://api.hostip.info/get_json.php';
        var dfr = $.Deferred();

        dfr.then(function(data) {
            IP_ADDRESS = data.ip;
            return data;
        });

        if (window.XDomainRequest) {
            // handle IE8
            var xmlhttp = new XDomainRequest();
            xmlhttp.open('GET', url, false);
            xmlhttp.onload = function () {
                dfr.resolve($.parseJSON(xmlhttp.responseText));
            };
            xmlhttp.send();
        } else {
            $.getJSON(url).then(dfr.resolve);
        }
    }

    function jqueryLoadHandler() {
        // Restore $ and window.jQuery to their previous values and store the
        // new jQuery in our local jQuery variable
        $ = jQuery = window.jQuery.noConflict(true);
        if (window.jQuery === undefined) {
            window.jQuery = $;
        }
        window.jQuery_c4all = $;

        main();
    }

    function makeCrossDomainPost(url, params) {
        // Add the iframe with a unique name
        var iframe = document.createElement('iframe');

        document.body.appendChild(iframe);
        iframe.id = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
            return v.toString(16);
        });
        iframe.source = 'about:blank';
        iframe.style.display = 'none';

        // construct a form with hidden inputs, targeting the iframe
        var form = document.createElement('form');
        form.action = url;
        form.method = 'POST';

        // repeat for each parameter
        for (var param in params) {
            var input = document.createElement('input');
            input.type = 'hidden';
            input.name = param;
            input.value = params[param];
            form.appendChild(input);
        }

        var inputIframeId = document.createElement('input');
        inputIframeId.type = 'hidden';
        inputIframeId.name = 'iframeId';
        inputIframeId.value = iframe.id;
        form.appendChild(inputIframeId);

        var iframeDocument=(iframe.contentWindow || iframe.contentDocument);
        if (iframeDocument.document) {
            iframeDocument=iframeDocument.document;
        }
        iframeDocument.open();
        iframeDocument.close();

        iframeDocument.body.appendChild(form);


        form.submit();

        return false;
    }


    function makeCrossDomainGet(url, params) {
        return jQuery.ajax({
            type: 'GET',
            url: url,
            data: params,
            dataType: 'jsonp',
            crossDomain: true
        }).then(function (data) {
            var id = '#' + data.html_container_name;
            jQuery(id).html(data.html);
            return data;
        });
    }

    function makeUrl(action) {
        var path = '';
        if (jQuery.inArray(action, ['like', 'dislike']) >= 0) {
            path = 'thread/' + THREAD + '/' + action;
        } else {
            path = action;
        }
        return '/' + path;
    }

    function doPost(action, params) {
        return makeCrossDomainPost(C4ALL_SERVER + makeUrl(action), params);
    }

    function doGet(action, params) {
        return makeCrossDomainGet(C4ALL_SERVER + makeUrl(action), params);
    }

    function fetchHtml(part, add_params) {
        var params = {
            thread: THREAD,
            domain: DOMAIN
        };

        for (var param in add_params){
            params[param] = add_params[param];
        }

        var dfrs = [];

        if(COMMENTS_ENABLED === true) {
            if (!part) {
                dfrs.push(doGet('header', params));
                dfrs.push(doGet('comments', params));
                dfrs.push(doGet('footer', params));
            } else {
                dfrs.push(doGet(part, params));
            }
            return $.when.apply($.when, dfrs);
        }
        return undefined;
    }


    function sendComment() {
        var poster_name = '';
        if ($('#display-name').length > 0){
            poster_name = $('#display-name').val();
        }

        var params = {
            poster_name: poster_name,
            text: sanitizeSpellcheckedHtml($('#comment-input-ceditable').html()),
            thread: THREAD,
            domain: DOMAIN,
            ip_address: IP_ADDRESS
        };

        if (!params.text || (!params.poster_name && $('#display-name').length > 0)) {
            return;
        }

        doPost('comment', params);
        $('#comment-input-ceditable').html('');
        return false;
    }


    function loginAndComment(action) {
        var params = {};

        if (action === 'register'){
            $('.register-box input').each(function(i, el) {
                params[el.name] = el.value;
            });
        }
        else{
            $('.login-box input').each(function(i, el) {
                params[el.name] = el.value;
            });
        }

        params.avatar_num = $('.avatar-selector img').data('avatar_num') || 6; // 6 - green diamond - default avatar

        if (!params.email || !params.password) {
            return;
        }

        if (action === 'register' && (!params.password2 || !params.full_name)) {
            return;
        }

        return doPost(action, params);
    }

    function toggleAvatarSelector(e) {
        e.stopPropagation();
        $('#c4all_avatar_selection_box').fadeToggle(100);
    }

    function closeAvatarSelector() {
        $('#c4all_avatar_selection_box').fadeOut(100);
    }

    function avatarSelect(e) {
        e.stopPropagation();
        var el = $(this).children('img');
        var num = el.data('num');
        doPost('set_avatar', { avatar_num: num });
        $('#avatar').attr('src', el[0].src).data('avatar_num', num);
        $('#c4all_avatar_selection_box .state-active').removeClass('state-active');
        var selected_img = $("#c4all_avatar_selection_box .button.naked [data-num='" + num + "']");
        selected_img.closest('button').addClass('state-active');
        closeAvatarSelector();
        return false;
     }

    function logout() {
        doPost('logout');
        return false;
    }

    function commentFeedback() {
        var el = $(this);
        var commentId = $(this).closest('.comment-list-item').data('comment-id');
        var action = el.data('action');
        var url = C4ALL_SERVER + '/comment/' + commentId + '/' + action;
        makeCrossDomainPost(url, { 'domain': DOMAIN });
        return false;
    }

    function insertEmoticon() {

        var rangeInEditor = function ($el) {
            var range, container;
            if (window.getSelection) {
                range = window.getSelection().getRangeAt(0);
                container = range.commonAncestorContainer;
            } else {
                // IE
                range = document.selection.createRange();
                container = range.parentElement();
            }
            var comment_box = $el[0];
            return ((container === comment_box) || (jQuery.contains(comment_box, container)));
        };

        var cursorToEnd = function ($el) {
            var el = $el[0];
            var range;
            if (window.getSelection && document.createRange) {
                var sel = window.getSelection();
                range = document.createRange();
                range.setStart(el, 0);
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);
            } else {
                // IE
                range = document.body.createTextRange();
                range.moveToElementText(el);
                range.collapse(true);
                range.select();
            }
            return range;
        };

        var insertNode = function ($el, node) {
            document.getElementById('comment-input-ceditable').focus();
            var sel, range, lastChar = '';
            if (window.getSelection) {
                sel = window.getSelection();
                range = sel.getRangeAt(0);
                lastChar = range.startContainer.textContent.length ? range.startContainer.textContent.slice(-1) : '';

                var hasSpaceBefore = lastChar.match(/\s/) || lastChar === '';
                var spaceNodeBefore = document.createTextNode('\u00A0'); // unicode space
                var spaceNodeAfter = document.createTextNode('\u00A0');
                if (!rangeInEditor($el)) {
                    range = cursorToEnd($el);
                }
                if (!range.collapsed && range.deleteContents) {
                    range.deleteContents();
                }
                range.insertNode(spaceNodeAfter);
                range.insertNode(node);
                if (!hasSpaceBefore) {
                    range.insertNode(spaceNodeBefore);
                }
                range.setEndAfter(spaceNodeAfter);
                range.setStartAfter(spaceNodeAfter);
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);
            } else {
                // IE
                sel = document.selection;
                range = sel.createRange();
                var markerId = 'marker_' + Date.now();
                range.collapse(false);
                range.pasteHTML('\u00A0' + node.outerHTML + '\u00A0' + '<span id="' + markerId + '"></span>');
                var markerEl = document.getElementById(markerId);
                range.moveToElementText(markerEl);
                range.select();
                markerEl.parentNode.removeChild(markerEl);
            }
        };
        var editable = $('#comment-input-ceditable');
        selections.load(editable[0], selections.lastSelection);

        insertNode(editable, $(this).find('img').clone()[0]);
        selections.save(editable[0]);
        return false;
    }

    function switchLoginSignUp(){
        var el = $(this);
        if (el.context.id == 'login-switch'){
            $('#signup-container').addClass('visually-hidden');
            $('#login-container').removeClass('visually-hidden');
        }
        else{
            $('#signup-container').removeClass('visually-hidden');
            $('#login-container').addClass('visually-hidden');
        }
        return false;
    }

    function clearLoginSignupInput(){
        $('.login-register-box input').val('');
        return false;
    }

    function responsive_design(){
        var width = $('#c4all-widget-container').parent().width();
        if (width < MIN_PARENT_WIDTH) {
            $('#c4all-widget-container').addClass('narrow-view');
            $('#c4all-widget-container').removeClass('normal-view');
        } else {
            $('#c4all-widget-container').addClass('normal-view');
            $('#c4all-widget-container').removeClass('narrow-view');
        }
    }

    function bindEvents() {
        var containerId = '#c4all-widget-container';
        var userInfoContainerClass = '.ctrl-user-registration';
        var keyupTimeout;

        var handlers = {
            '#c4all_like_thread_button': function() {
                return doPost('like');
            },
            '#c4all_dislike_thread_button': function() {
                return doPost('dislike');
            },
            '#c4all_send_comment_button': sendComment,
            '.deselected-auth-option a': function () {
                var container = $(containerId);
                var userInfoContainer = $(userInfoContainerClass, container);

                if ($('.user-login').length){
                    userInfoContainer.addClass('user-register').removeClass('user-no-action user-login');
                }
                else{
                    userInfoContainer.addClass('user-login').removeClass('user-no-action user-register');
                }

                return false;
            },
            '#c4all_login_button': function () {
                return loginAndComment('login');
            },
            '#c4all_register_button': function () {
                return loginAndComment('register');
            },
            '#c4all_logout': logout,
            '#c4all_select_avatar': function(e){
                toggleAvatarSelector(e);
                return false;
            },
            '.toolbar-action': insertEmoticon,
            '#c4all_avatar_selection_box .button.naked': avatarSelect,
            '#login-switch': switchLoginSignUp,
            '#signup-switch': switchLoginSignUp,
            '.ctrl-comment-feedback': commentFeedback,
            '.c4all_cancel_login': clearLoginSignupInput,
            '#make-comment-link': function() {
                $('#comment-input-ceditable').focus();
                return false;
            },
            '.button-no-action': function(e){
                e.preventDefault();
            },
            '#anchor-admin': function(){
                window.open(this.href);
                return false;
            },
            '#btn-viev-all-comments': get_all_comments,
        };

        for (var handler in handlers) {
            $(containerId).on('click', handler, handlers[handler]);
        }

        $(document).bind('click', function () {
            if ($('#c4all_avatar_selection_box').is(':visible')){
                closeAvatarSelector();
            }
        });

        $(window).resize(function() {
            responsive_design();
        });

        $('#comments_footer').on('click keyup', '#comment-input-ceditable', function() {
            var el = this;
            clearTimeout(keyupTimeout);
            keyupTimeout = setTimeout(function() {
                selections.save(el);
            }, 200);
        });

        // stopping enter button event from propagation is needed for sites
        // which host all of the HTML body code in a form. since every enter
        // keypress submits form, we want to stop this from happening in
        // certain situations (e.g. when user wants newline in content
        // editable). stopEnterPropagationElements is a list of elements that
        // are affected by form submit behaviour, so we assign them onkeypress
        // event handler which prevents submit action from happening.
        var stopEnterPropagationElements = ["#comment-input-ceditable", "#display-name",
            "#display-full_name", "#c4all-email", "#c4all-password", "#c4all-password2"
        ];

        for (var i = 0; i < stopEnterPropagationElements.length; i++){
            var id = stopEnterPropagationElements[i];
            $(id).on('keypress', stopEnterKeypressAction);
        }

        assignReadSpeakerToEditor();
        assignReadSpeakerToComments();
    }

    function assignReadSpeakerToComments(){
        $("a.ttl-action").each(function(idx, el){
            el.id = $(el).data('comment-id');
            params = {
                customerid: $(el).data('customer-id'),
                lang: 'sv_se',
                readid: $(el).data('comment-id'),
                url: document.location.href
            };
            var url_params = $.param(params);
            var rs_href = READSPEAKER_BASE_URL + url_params;
            $(el).attr('href', rs_href);
            $(el).on('click', function(){
                readpage(this.href, "player-" + this.id);
                return false;
            });
        });
    }

    function assignReadSpeakerToEditor(){
        var el = $("#ttl-text-editor-btn");
        params = {
            customerid: el.data('customer-id'),
            lang: 'sv_se',
            readid: "comment-input-ceditable",
            url: document.location.href
        };
        var url_params = $.param(params);
        var rs_href = READSPEAKER_BASE_URL + url_params;
        el.on('click', {"rs_href": rs_href}, function(e){
            readpage(e.data.rs_href, "player-content-editable");
            return false;
        });
    }

    function stopEnterKeypressAction(e){
        if (e.keyCode == 13){
            e.stopImmediatePropagation();
        }
    }

    function get_all_comments(){
        $.when(fetchHtml("comments", {'all': true})).then(assignReadSpeakerToComments);
        return false;
    }

    function buildHtml() {
        // divide main container to 3 parts
        jQuery('#c4all-widget-container')
            .append('<div id="comments_header"></div>')
            .append('<div id="comments_container"></div>')
            .append('<div id="comments_footer"></div>');

        responsive_design();
    }


    function receiveMessage(e) {
        if (e.origin != C4ALL_SERVER) {
            return;
        }
        var data = JSON.parse(e.data);

        var response = data.resp_data;

        try {
            response = $.parseJSON(data.resp_data);

            if ((data.status_code === 200) && response.placement && response.content) {
                $('#' + response.placement).html(response.content);
            }
            if (response.placement === "comments_container"){
                assignReadSpeakerToComments();
            }
        } catch (e) { }

        if (data.iframeId){
            $('#'.concat(data.iframeId)).remove();
        }

        switch (data.request_path) {
        case '/comment':
            var el = $(".comment.my-comment.comment-list-item[data-comment-id='" + response.comment_id + "']");
            var extraPadding = 25;
            $('html, body').animate({
                scrollTop: el.offset().top - window.innerHeight + el.height() + extraPadding
            }, 500);
            break;
        case '/set_avatar':
            $('#c4all_select_avatar').focus();
            break;
        case '/logout':
            $.when(fetchHtml('comments')).then(assignReadSpeakerToComments);
            $.when(fetchHtml('footer')).then(assignMagnificPopup).then(assignJquerySpellChecker).then(assignReadSpeakerToEditor);
            break;
        case '/login':
            $.when(fetchHtml('comments')).then(assignReadSpeakerToComments);
            $.when(fetchHtml('footer')).then(assignMagnificPopup).then(assignJquerySpellChecker).then(assignReadSpeakerToEditor);
            break;
        case '/register':
            sendComment();
            $.when(fetchHtml('footer')).then(assignMagnificPopup).then(assignJquerySpellChecker).then(assignReadSpeakerToEditor);
            break;
        case '/spellcheck/incorrect_words':
            handleIncorrectWords(response);
            break;
        case '/spellcheck/suggestions':
            handleWordSuggestions(response);
            break;
        case makeUrl('like'):
        case makeUrl('dislike'):
            if (data.status_code !== 200) {
                $('.ctrl-error-like').html(response.content);
            }
        }
    }

    function handleIncorrectWords(resp){
        var func = spellchecker.onCheckWords();
        func(resp);
    }

    function handleWordSuggestions(resp){
        spellchecker.suggestBox.onGetWords(resp.data);
    }

    // removes span tags if any (span tags appear
    // as a result of a spellchecking process)
    function sanitizeSpellcheckedHtml(html){
        return html.replace(/(<(?!(img|\/img|br|\/br)).+?>)/ig, "");
    }

    function fetchThreadId(){
        var params = {
            thread: THREAD_URL,
            domain: DOMAIN,
            selector_title: $(TITLE_SELECTOR).text(),
            page_title: $('title').text(),
            h1_title: $('h1').first().text()
        };

        var url = C4ALL_SERVER + '/thread_info';
        return makeCrossDomainGet(url, params).then(function(data) {
            THREAD = data.thread_id;
            COMMENTS_ENABLED = data.comments_enabled;
            SPELLCHECK_ENABLED = data.spellcheck_enabled;
            SPELLCHECK_LOCALIZATION = data.spellcheck_localization;
            return data;
        });
    }

    var selections = {};

    if (window.getSelection && document.createRange) {
        selections.save = function(containerEl) {
            var range = window.getSelection().getRangeAt(0);
            var preSelectionRange = range.cloneRange();
            preSelectionRange.selectNodeContents(containerEl);
            preSelectionRange.setEnd(range.startContainer, range.startOffset);
            var start = preSelectionRange.toString().length;

            selections.lastSelection = {
                start: start,
                end: start + range.toString().length
            };

            return selections.lastSelection;
        };

        selections.load = function(containerEl, savedSel) {
            var charIndex = 0, range = document.createRange();
            range.setStart(containerEl, 0);
            range.collapse(true);
            var nodeStack = [containerEl], node, foundStart = false, stop = false;

            while (!stop && (node = nodeStack.pop())) {
                if (node.nodeType == 3) {
                    var nextCharIndex = charIndex + node.length;
                    if (!foundStart && savedSel.start >= charIndex && savedSel.start <= nextCharIndex) {
                        range.setStart(node, savedSel.start - charIndex);
                        foundStart = true;
                    }
                    if (foundStart && savedSel.end >= charIndex && savedSel.end <= nextCharIndex) {
                        range.setEnd(node, savedSel.end - charIndex);
                        stop = true;
                    }
                    charIndex = nextCharIndex;
                } else {
                    var i = node.childNodes.length;
                    while (i--) {
                        nodeStack.push(node.childNodes[i]);
                    }
                }
            }

            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        };
    } else if (document.selection) {
        selections.save = function(containerEl) {
            var selectedTextRange = document.selection.createRange();
            var preSelectionTextRange = document.body.createTextRange();
            preSelectionTextRange.moveToElementText(containerEl);
            preSelectionTextRange.setEndPoint('EndToStart', selectedTextRange);
            var start = preSelectionTextRange.text.length;
            var html = $('<div>' + preSelectionTextRange.htmlText + '</div>');
            var elementsCount = html.find('> *').size();

            selections.lastSelection = {
                start: start,
                end: start + selectedTextRange.text.length + elementsCount
            };

            return selections.lastSelection;
        };

        selections.load = function(containerEl, savedSel) {
            var textRange = document.body.createTextRange();
            textRange.moveToElementText(containerEl);
            textRange.collapse(true);
            textRange.moveEnd('character', savedSel.end);
            textRange.moveStart('character', savedSel.start);
            textRange.select();
        };
    }

    function main() {
        fetchThreadId();
        $('<link>', {
            rel: 'stylesheet',
            type: 'text/css',
            href: C4ALL_SERVER + '/static/css/style.css'
        }).appendTo('head');

        $('<link>', {
            rel: 'stylesheet',
            type: 'text/css',
            href: C4ALL_SERVER + '/static/js/magnific-popup/magnific-popup.css'
        }).appendTo('head');

        loadReadSpeaker();
    }

    function magnificPopupAfterLoad (){
        if (!window.addEventListener){
            window.attachEvent('onmessage', receiveMessage);
        }
        else{
            window.addEventListener('message', receiveMessage, false);
        }

        $(function() {
            $.when(fetchThreadId(), myIP())
                .then(buildHtml)
                .then(fetchHtml)
                .then(bindEvents)
                .then(assignMagnificPopup)
                .then(function(){
                    if (SPELLCHECK_ENABLED){
                        loadJquerySpellChecker();
                    }
                })
                .then(assignReadSpeakerConf);
        });
    }

    function loadJquerySpellChecker(){
        $('<link>', {
            rel: 'stylesheet',
            type: 'text/css',
            href: C4ALL_SERVER + '/static/js/jquery-spellchecker/src/css/jquery.spellchecker.css'
        }).appendTo('head');

        var script_tag = document.createElement('script');
            script_tag.setAttribute('type', 'text/javascript');
            script_tag.setAttribute('src',
                C4ALL_SERVER + '/static/js/jquery-spellchecker/src/js/jquery.spellchecker.js');
            if (script_tag.readyState) {
                script_tag.onreadystatechange = function () { // For old versions of IE
                    if (this.readyState === 'complete' || this.readyState === 'loaded') {
                        assignJquerySpellChecker();
                    }
                };
            } else { // Other browsers
                script_tag.onload = assignJquerySpellChecker;
            }
            // Try to find the head, otherwise default to the documentElement
            (document.getElementsByTagName('head')[0] || document.documentElement).appendChild(script_tag);
    }

    function loadMagnificPopup(){
        var script_tag = document.createElement('script');
            script_tag.setAttribute('type', 'text/javascript');
            script_tag.setAttribute('src',
                C4ALL_SERVER + '/static/js/magnific-popup/jquery.magnific-popup.js');
            if (script_tag.readyState) {
                script_tag.onreadystatechange = function () { // For old versions of IE
                    if (this.readyState === 'complete' || this.readyState === 'loaded') {
                        magnificPopupAfterLoad();
                    }
                };
            } else { // Other browsers
                script_tag.onload = magnificPopupAfterLoad;
            }
            // Try to find the head, otherwise default to the documentElement
            (document.getElementsByTagName('head')[0] || document.documentElement).appendChild(script_tag);
    }

    function assignMagnificPopup(){
            $('.popup-with-zoom-anim').magnificPopup({
                type: 'inline',
                fixedContentPos: false,
                fixedBgPos: true,
                overflowY: 'auto',
                closeBtnInside: true,
                preloader: false,
                midClick: true,
                removalDelay: 300,
                mainClass: 'my-mfp-zoom-in'
            });
    }

    function assignJquerySpellChecker(){
        // Create a new spellchecker instance
        spellchecker = new $.SpellChecker('#comment-input-ceditable', {
            parser: 'html',
            suggestBox: {
                position: 'above'
            },
            local: SPELLCHECK_LOCALIZATION
        });

        spellchecker.webservice.makeRequest = function(action, params){
            doPost(action, params);
        };

        spellchecker.webservice.checkWords = function(text){
            this.makeRequest("spellcheck/incorrect_words", {'text': sanitizeNewlines($('#comment-input-ceditable').html())});
        };

        spellchecker.webservice.getSuggestions = function(word){
            this.makeRequest("spellcheck/suggestions", {'word': word});
        };

        $("#button-spellcheck").on('click', function(){
            if (SPELLCHECK_ENABLED){
                spellchecker.check();
            }
            return false;
        });
    }

    function sanitizeNewlines(html){
        return html.replace(/<br>/g, " ");
    }

    function assignReadSpeakerConf(){
        window.ReadSpeaker.init();
    }

    function loadReadSpeaker(){
        window.rsConf = {params: 'http://f1.eu.readspeaker.com/script/5610/ReadSpeaker.js?pids=embhl', general: {usePost: true}};

        if (window.ReadSpeaker === undefined || window.ReadSpeaker.baseUrl != "http://f1.eu.readspeaker.com/script/5610/") {

            var script_tag = document.createElement('script');
            script_tag.setAttribute('type', 'text/javascript');
            script_tag.setAttribute('src', 'http://f1.eu.readspeaker.com/script/5610/ReadSpeaker.js?pids=embhl');

            if (script_tag.readyState) {
                script_tag.onreadystatechange = function () { // For old versions of IE
                    if (this.readyState === 'complete' || this.readyState === 'loaded') {
                        loadMagnificPopup();
                    }
                };
            } else { // Other browsers
                script_tag.onload = loadMagnificPopup;
            }
            // Try to find the head, otherwise default to the documentElement
            (document.getElementsByTagName('head')[0] || document.documentElement).appendChild(script_tag);
        }
        else{
            loadMagnificPopup();
        }
    }

    loadJquery();
})();
