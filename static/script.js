const form        = document.getElementById('predictForm');
const runBtn      = document.getElementById('runBtn');
const resultCard  = document.getElementById('resultCard');
const errorCard   = document.getElementById('errorCard');
const errorMsg    = document.getElementById('errorMsg');
const minutesVal  = document.getElementById('minutesVal');
const resultTag   = document.getElementById('resultTag');
const resultTime  = document.getElementById('resultTime');
const ticker      = document.getElementById('ticker');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn    = document.getElementById('resetBtn');

const routeProgress = document.getElementById('routeProgress');
const courierDot    = document.getElementById('courierDot');
const routePath      = document.getElementById('routePath');
const PATH_LEN = routePath.getTotalLength();

let lastPayload = null;

function animateRoute(fraction){
  const dash = Math.max(4, PATH_LEN * fraction);
  routeProgress.style.strokeDasharray = `${dash} ${PATH_LEN}`;
  const pt = routePath.getPointAtLength(PATH_LEN * fraction);
  courierDot.setAttribute('cx', pt.x);
  courierDot.setAttribute('cy', pt.y);
}

function setTicker(text, live=false){
  ticker.innerHTML = live ? `<span class="live">${text}</span>` : `<span>${text}</span>`;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorCard.hidden = true;
  runBtn.classList.add('loading');
  runBtn.disabled = true;
  setTicker('CALCULATING ROUTE ETA…', true);
  animateRoute(0.15);

  const fd = new FormData(form);
  const payload = Object.fromEntries(fd.entries());

  try{
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if(!data.ok){
      throw new Error(data.error || 'Prediction failed');
    }

    lastPayload = data;
    animateRoute(1);

    minutesVal.textContent = data.minutes;
    resultTag.textContent  = data.label;
    resultTag.className    = `result-tag ${data.css_class}`;
    resultTime.textContent = data.generated_at;
    resultCard.hidden = false;
    resultCard.classList.remove('result-card');
    void resultCard.offsetWidth;
    resultCard.classList.add('result-card');

    setTicker(`ETA ${data.minutes} MIN · ${data.distance_km} KM · ${data.label.toUpperCase()}`, true);
    resultCard.scrollIntoView({behavior:'smooth', block:'nearest'});

  }catch(err){
    animateRoute(0);
    setTicker('PREDICTION FAILED — CHECK INPUTS');
    errorMsg.textContent = err.message;
    errorCard.hidden = false;
  }finally{
    runBtn.classList.remove('loading');
    runBtn.disabled = false;
  }
});

downloadBtn.addEventListener('click', async () => {
  if(!lastPayload) return;
  const res = await fetch('/api/report', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(lastPayload)
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'delivery_prediction.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

resetBtn.addEventListener('click', () => {
  resultCard.hidden = true;
  animateRoute(0);
  setTicker('AWAITING ORDER DETAILS');
});
