// ==UserScript==
// @name         Muse AI × Gemini Pro Companion
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Outsource deep reasoning, vision, and document analysis to your active Gemini Pro Subscription from muse.ai & Meta AI
// @match        https://muse.ai/*
// @match        https://*.muse.ai/*
// @match        https://*.meta.ai/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setClipboard
// ==/UserScript==

(function() {
    'use strict';

    const BRIDGE_URL = "http://127.0.0.1:8000/v1/chat/completions";

    // Inject Styles
    const style = document.createElement('style');
    style.textContent = `
        #gemini-floating-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4285F4, #9B51E0);
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 999999;
            color: white;
            font-weight: bold;
            font-family: system-ui, sans-serif;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        #gemini-floating-btn:hover {
            transform: scale(1.08);
            box-shadow: 0 6px 20px rgba(66, 133, 244, 0.5);
        }
        #gemini-modal {
            position: fixed;
            bottom: 84px;
            right: 24px;
            width: 420px;
            max-height: 520px;
            background: #1e1e24;
            color: #f0f0f0;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.6);
            display: none;
            flex-direction: column;
            z-index: 999999;
            font-family: system-ui, sans-serif;
            overflow: hidden;
        }
        #gemini-modal-header {
            background: #282832;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        #gemini-modal-body {
            padding: 14px 16px;
            overflow-y: auto;
            flex: 1;
            font-size: 13px;
            line-height: 1.5;
        }
        #gemini-modal-input {
            width: 100%;
            box-sizing: border-box;
            background: #141418;
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 13px;
            resize: none;
            height: 64px;
            margin-bottom: 8px;
        }
        .gemini-btn {
            background: #4285F4;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
        }
        .gemini-btn:hover {
            background: #3367D6;
        }
        #gemini-output {
            margin-top: 10px;
            background: #141418;
            padding: 10px;
            border-radius: 8px;
            white-space: pre-wrap;
            max-height: 220px;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.08);
            font-size: 12px;
        }
    `;
    document.head.appendChild(style);

    // Create DOM Elements
    const btn = document.createElement('div');
    btn.id = 'gemini-floating-btn';
    btn.innerHTML = '✦';
    btn.title = 'Consult Gemini 3.1 Pro (Alt+G)';
    document.body.appendChild(btn);

    const modal = document.createElement('div');
    modal.id = 'gemini-modal';
    modal.innerHTML = `
        <div id="gemini-modal-header">
            <span>Google Gemini 3.1 Pro Companion</span>
            <span style="cursor:pointer; opacity:0.6;" id="gemini-close">✕</span>
        </div>
        <div id="gemini-modal-body">
            <textarea id="gemini-modal-input" placeholder="Ask Gemini Pro for reasoning, proof, or second opinion... (or highlight text on Muse and press Alt+G)"></textarea>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <button class="gemini-btn" id="gemini-submit">Ask Gemini Pro</button>
                <button class="gemini-btn" style="background:#555;" id="gemini-copy">Copy Output</button>
            </div>
            <div id="gemini-output" style="display:none;"></div>
        </div>
    `;
    document.body.appendChild(modal);

    const input = document.getElementById('gemini-modal-input');
    const output = document.getElementById('gemini-output');

    function toggleModal() {
        if (modal.style.display === 'flex') {
            modal.style.display = 'none';
        } else {
            modal.style.display = 'flex';
            const sel = window.getSelection().toString().trim();
            if (sel) {
                input.value = sel;
            }
            input.focus();
        }
    }

    btn.addEventListener('click', toggleModal);
    document.getElementById('gemini-close').addEventListener('click', () => modal.style.display = 'none');

    // Global Shortcut Alt+G
    window.addEventListener('keydown', (e) => {
        if (e.altKey && (e.key === 'g' || e.key === 'G')) {
            e.preventDefault();
            toggleModal();
        }
    });

    // Submit Query
    document.getElementById('gemini-submit').addEventListener('click', async () => {
        const query = input.value.trim();
        if (!query) return;

        output.style.display = 'block';
        output.textContent = 'Thinking with Gemini 3.1 Pro...';

        try {
            const resp = await fetch(BRIDGE_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: 'gemini-3.1-pro-high',
                    messages: [{ role: 'user', content: query }],
                    stream: false
                })
            });
            const data = await resp.json();
            const reply = data.choices?.[0]?.message?.content || 'No response';
            output.textContent = reply;
        } catch (err) {
            output.textContent = 'Error contacting Gemini Bridge at http://127.0.0.1:8000. Ensure bridge is running.';
        }
    });

    document.getElementById('gemini-copy').addEventListener('click', () => {
        if (output.textContent && output.textContent !== 'Thinking with Gemini 3.1 Pro...') {
            navigator.clipboard.writeText(output.textContent);
            alert('Gemini response copied to clipboard! Paste it into Muse.');
        }
    });

})();
