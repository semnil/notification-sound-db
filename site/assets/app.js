(() => {
  const search = document.querySelector('#search');
  const source = document.querySelector('#source-filter');
  const event = document.querySelector('#event-filter');
  const rows = [...document.querySelectorAll('#measurement-rows tr')];
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#no-results');
  if (!search || !source || !event || !count || !empty) return;

  const normalize = (value) => value.toLocaleLowerCase().normalize('NFKC');
  const update = () => {
    const query = normalize(search.value.trim());
    let visible = 0;
    for (const row of rows) {
      const matches = (!query || normalize(row.dataset.search).includes(query))
        && (!source.value || row.dataset.source === source.value)
        && (!event.value || row.dataset.event === event.value);
      row.hidden = !matches;
      if (matches) visible += 1;
    }
    count.textContent = String(visible);
    empty.hidden = visible !== 0;
    const url = new URL(window.location.href);
    query ? url.searchParams.set('q', search.value.trim()) : url.searchParams.delete('q');
    source.value ? url.searchParams.set('source', source.value) : url.searchParams.delete('source');
    event.value ? url.searchParams.set('event', event.value) : url.searchParams.delete('event');
    history.replaceState(null, '', url);
  };
  const params = new URLSearchParams(window.location.search);
  search.value = params.get('q') || '';
  source.value = params.get('source') || '';
  event.value = params.get('event') || '';
  search.addEventListener('input', update);
  source.addEventListener('change', update);
  event.addEventListener('change', update);
  update();
})();
