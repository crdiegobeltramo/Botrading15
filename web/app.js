(() => {
  const backtestTabBtn = document.getElementById('tab-backtest');
  const liveTabBtn = document.getElementById('tab-live');
  const backtestTab = document.getElementById('backtest');
  const liveTab = document.getElementById('live');

  function switchTab(tab) {
    if (tab === 'backtest') {
      backtestTabBtn.classList.add('active');
      liveTabBtn.classList.remove('active');
      backtestTab.classList.add('active');
      liveTab.classList.remove('active');
    } else {
      liveTabBtn.classList.add('active');
      backtestTabBtn.classList.remove('active');
      liveTab.classList.add('active');
      backtestTab.classList.remove('active');
    }
  }

  backtestTabBtn.addEventListener('click', () => switchTab('backtest'));
  liveTabBtn.addEventListener('click', () => switchTab('live'));

  // Strategy param toggles
  const stratSelect = document.getElementById('strategy-select');
  const paramsSma = document.getElementById('params-sma');
  const paramsBb = document.getElementById('params-bbands');
  stratSelect.addEventListener('change', () => {
    const v = stratSelect.value;
    paramsSma.classList.toggle('hidden', v !== 'sma_crossover');
    paramsBb.classList.toggle('hidden', v !== 'bbands');
  });

  const liveStratSelect = document.getElementById('live-strategy-select');
  const liveParamsSma = document.getElementById('live-params-sma');
  const liveParamsBb = document.getElementById('live-params-bbands');
  liveStratSelect.addEventListener('change', () => {
    const v = liveStratSelect.value;
    liveParamsSma.classList.toggle('hidden', v !== 'sma_crossover');
    liveParamsBb.classList.toggle('hidden', v !== 'bbands');
  });

  // Default dates: last 300 days
  const btForm = document.getElementById('backtest-form');
  const today = new Date();
  const past = new Date(Date.now() - 1000 * 60 * 60 * 24 * 300);
  btForm.elements['start'].value = past.toISOString().slice(0, 10);
  btForm.elements['end'].value = today.toISOString().slice(0, 10);

  let equityChart;
  function renderEquityChart(payload) {
    const ctx = document.getElementById('equityChart');
    const labels = payload.equity.timestamps.map(ts => new Date(ts));
    const data = payload.equity.values;
    if (equityChart) equityChart.destroy();
    equityChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Equidad',
            data,
            borderColor: '#1f6feb',
            fill: false,
            tension: 0.1,
          }
        ]
      },
      options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        scales: {
          x: { type: 'time', time: { unit: 'day' } },
          y: { ticks: { callback: (v) => v } }
        }
      }
    });
  }

  function metricsHtml(m) {
    const round = (x, n=4) => (x === null || x === undefined || Number.isNaN(x)) ? '-' : Number(x).toFixed(n);
    return `
      <div class="row">
        <div><strong>Total Return:</strong> ${round(m.total_return)}</div>
        <div><strong>CAGR:</strong> ${round(m.cagr)}</div>
        <div><strong>Sharpe:</strong> ${round(m.sharpe)}</div>
        <div><strong>Max Drawdown:</strong> ${round(m.max_drawdown)}</div>
      </div>
      <div class="row">
        <div><strong># Trades:</strong> ${m.num_trades ?? '-'}</div>
        <div><strong>Win Rate:</strong> ${round(m.win_rate)}</div>
        <div><strong>Avg Trade:</strong> ${round(m.avg_trade_return)}</div>
      </div>
    `;
  }

  btForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const payload = {
      symbol: form.elements['symbol'].value.trim(),
      interval: form.elements['interval'].value,
      start: form.elements['start'].value,
      end: form.elements['end'].value,
      strategy: form.elements['strategy'].value,
      source: form.elements['source'].value,
      initial_capital: Number(form.elements['initial_capital'].value),
      fee: Number(form.elements['fee'].value),
      fast: Number(form.elements['fast'].value),
      slow: Number(form.elements['slow'].value),
      window: Number(form.elements['window'].value),
      num_std: Number(form.elements['num_std'].value),
    };
    const res = await fetch('/api/backtest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const out = document.getElementById('bt-metrics');
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      out.innerHTML = `<div style="color:#b00">Error: ${err.detail || res.status}</div>`;
      return;
    }
    const data = await res.json();
    out.innerHTML = metricsHtml(data.metrics);
    renderEquityChart(data);
  });

  const liveForm = document.getElementById('live-form');
  const btnSignal = document.getElementById('btn-signal');
  const btnOrder = document.getElementById('btn-order');
  const liveOut = document.getElementById('live-output');

  function livePayload() {
    return {
      symbol: liveForm.elements['symbol'].value.trim(),
      interval: liveForm.elements['interval'].value,
      strategy: liveForm.elements['strategy'].value,
      source: liveForm.elements['source'].value,
      lookback_days: Number(liveForm.elements['lookback_days'].value),
      fast: Number(liveForm.elements['fast'].value),
      slow: Number(liveForm.elements['slow'].value),
      window: Number(liveForm.elements['window'].value),
      num_std: Number(liveForm.elements['num_std'].value),
      testnet: liveForm.elements['testnet'].checked,
      quote_qty: liveForm.elements['quote_qty'].value ? Number(liveForm.elements['quote_qty'].value) : undefined,
    };
  }

  btnSignal.addEventListener('click', async () => {
    const payload = livePayload();
    const res = await fetch('/api/live/signal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const text = await res.text();
    liveOut.textContent = text;
  });

  btnOrder.addEventListener('click', async () => {
    const payload = livePayload();
    if (!payload.quote_qty || payload.quote_qty <= 0) {
      alert('Define quote_qty para enviar una orden.');
      return;
    }
    const res = await fetch('/api/live/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const text = await res.text();
    liveOut.textContent = text;
  });
})();