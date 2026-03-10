/* Tarihten Liderlik - Frontend JavaScript */

// ============================================
// API Helper
// ============================================

const API = {
    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },
    async del(url) {
        const res = await fetch(url, { method: 'DELETE' });
        return res.json();
    }
};

function getData() {
    return window.TL_DATA || {};
}

// ============================================
// DURAK NOTES (durak_detay.html)
// ============================================

async function saveDurakNote(durakId) {
    const textarea = document.getElementById(`durak-note-${durakId}`);
    if (!textarea) return;

    await API.post('/api/durak/note', { durak_id: durakId, note: textarea.value });

    if (window.TL_DATA) {
        if (!window.TL_DATA.durak_notes) window.TL_DATA.durak_notes = {};
        window.TL_DATA.durak_notes[durakId] = textarea.value;
    }

    const saved = document.getElementById(`note-saved-${durakId}`);
    if (saved) {
        saved.classList.remove('hidden');
        setTimeout(() => saved.classList.add('hidden'), 2000);
    }
}

async function loadDurakNote(durakId) {
    await window.TL_READY;
    const textarea = document.getElementById(`durak-note-${durakId}`);
    if (!textarea) return;
    const notes = getData().durak_notes || {};
    if (notes[durakId]) {
        textarea.value = notes[durakId];
    }
}

// ============================================
// DURAK VISITED TRACKING
// ============================================

async function markDurakVisited(durakId) {
    const result = await API.post('/api/durak/visit', { durak_id: durakId });
    if (window.TL_DATA && result.visited_duraklar) {
        window.TL_DATA.visited_duraklar = result.visited_duraklar;
    }
    updateVisitedButton(durakId);
}

async function updateVisitedButton(durakId) {
    await window.TL_READY;
    const visited = getData().visited_duraklar || [];
    const btn = document.getElementById('mark-visited-btn');
    if (btn && visited.includes(durakId)) {
        btn.textContent = '\u2705 Tamamlandi';
        btn.classList.remove('bg-ottoman-green');
        btn.classList.add('bg-gray-400', 'cursor-default');
        btn.disabled = true;
    }
}

async function updateDurakProgress() {
    await window.TL_READY;
    const visited = getData().visited_duraklar || [];
    const total = 7;
    const percent = Math.round((visited.length / total) * 100);

    const bar = document.getElementById('durak-progress');
    const text = document.getElementById('durak-progress-text');
    if (bar) bar.style.width = percent + '%';
    if (text) text.textContent = `${visited.length}/${total}`;

    visited.forEach(id => {
        const status = document.querySelector(`.durak-status[data-durak="${id}"]`);
        const statusText = document.querySelector(`.durak-status-text[data-durak="${id}"]`);
        if (status) status.innerHTML = '\u2705';
        if (statusText) {
            statusText.textContent = 'Tamamlandi';
            statusText.classList.add('text-green-500');
            statusText.classList.remove('text-gray-400');
        }
        const card = document.getElementById(`durak-card-${id}`);
        if (card) card.classList.add('ring-2', 'ring-green-400');
    });
}

// ============================================
// HAP ANSWERS (hap.html, lider_detay.html)
// ============================================

async function saveHapAnswers(liderId) {
    const answers = [];
    document.querySelectorAll(`.hap-answer[data-lider="${liderId}"]`).forEach(ta => {
        answers[parseInt(ta.dataset.question)] = ta.value;
    });

    await API.post('/api/hap/save', { lider_id: liderId, answers: answers });

    if (window.TL_DATA) {
        if (!window.TL_DATA.hap_answers) window.TL_DATA.hap_answers = {};
        window.TL_DATA.hap_answers[liderId] = answers;
    }

    const saved = document.getElementById(`hap-saved-${liderId}`);
    if (saved) {
        saved.classList.remove('hidden');
        setTimeout(() => saved.classList.add('hidden'), 2000);
    }
}

async function loadHapAnswers(liderId) {
    await window.TL_READY;
    const hapData = getData().hap_answers || {};
    const answers = hapData[liderId] || hapData[String(liderId)] || [];
    document.querySelectorAll(`.hap-answer[data-lider="${liderId}"]`).forEach(ta => {
        const idx = parseInt(ta.dataset.question);
        if (answers[idx]) ta.value = answers[idx];
    });
}

// ============================================
// QUIZ - DURAK MINI QUIZ (durak_detay.html)
// ============================================

function checkAnswer(btn, selectedIndex, correctIndex) {
    const question = btn.closest('.quiz-question');
    if (question.classList.contains('answered')) return;
    question.classList.add('answered');

    const options = question.querySelectorAll('.quiz-option');
    options.forEach(opt => {
        opt.disabled = true;
        opt.classList.add('cursor-default');
        opt.classList.remove('hover:border-ottoman-gold', 'hover:bg-ottoman-cream/50');
    });

    if (selectedIndex === correctIndex) {
        btn.classList.add('quiz-correct');
        const feedback = question.querySelector('.quiz-feedback');
        if (feedback) {
            feedback.innerHTML = '\u2705 Dogru cevap!';
            feedback.classList.remove('hidden');
            feedback.classList.add('bg-green-50', 'text-green-700');
        }
    } else {
        btn.classList.add('quiz-wrong');
        options[correctIndex].classList.add('quiz-correct');
        const feedback = question.querySelector('.quiz-feedback');
        if (feedback) {
            feedback.innerHTML = '\u274c Yanlis. Dogru cevap isaretlendi.';
            feedback.classList.remove('hidden');
            feedback.classList.add('bg-red-50', 'text-red-700');
        }
    }

    const quizContainer = document.getElementById('durak-quiz');
    if (quizContainer) {
        const allQuestions = quizContainer.querySelectorAll('.quiz-question');
        const answeredQuestions = quizContainer.querySelectorAll('.quiz-question.answered');
        if (allQuestions.length === answeredQuestions.length) {
            let correct = 0;
            answeredQuestions.forEach(q => {
                const selectedOpt = q.querySelector('.quiz-correct:not(.quiz-wrong)');
                const wrongOpt = q.querySelector('.quiz-wrong');
                if (selectedOpt && !wrongOpt) correct++;
            });
            const durakId = quizContainer.dataset.durak;
            const result = document.getElementById(`quiz-result-${durakId}`);
            if (result) {
                result.classList.remove('hidden');
                result.querySelector('p').textContent = `Sonuc: ${correct}/${allQuestions.length} dogru cevap!`;
            }
        }
    }
}
