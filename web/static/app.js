(() => {
  const search = document.querySelector('#search');
  const source = document.querySelector('#source-filter');
  const event = document.querySelector('#event-filter');
  const body = document.querySelector('#measurement-rows');
  const tableWrap = document.querySelector('#measurement-table-wrap');
  const scrollControls = document.querySelector('#table-scroll-controls');
  const scrollLeftButton = document.querySelector('#table-scroll-left');
  const scrollRightButton = document.querySelector('#table-scroll-right');
  const rows = [...document.querySelectorAll('#measurement-rows tr')];
  const sortButtons = [...document.querySelectorAll('.sort-button')];
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#no-results');
  if (!search || !source || !event || !body || !tableWrap || !count || !empty) return;

  const normalize = (value) => value.toLocaleLowerCase().normalize('NFKC');
  const collator = new Intl.Collator(document.documentElement.lang || undefined, {
    numeric: true,
    sensitivity: 'base',
  });
  const originalOrder = new Map(rows.map((row, index) => [row, index]));
  const params = new URLSearchParams(window.location.search);
  const validSortKeys = new Set(sortButtons.map((button) => button.dataset.sortKey));
  let sortKey = validSortKeys.has(params.get('sort')) ? params.get('sort') : '';
  let sortDirection = params.get('direction') === 'desc' ? 'desc' : 'asc';

  const compareRows = (left, right, type) => {
    const leftValue = left.getAttribute(`data-sort-${sortKey}`) || '';
    const rightValue = right.getAttribute(`data-sort-${sortKey}`) || '';
    const leftNumber = Number(leftValue);
    const rightNumber = Number(rightValue);
    const leftMissing = type === 'number'
      ? leftValue === '' || !Number.isFinite(leftNumber)
      : leftValue === '';
    const rightMissing = type === 'number'
      ? rightValue === '' || !Number.isFinite(rightNumber)
      : rightValue === '';

    if (leftMissing !== rightMissing) return leftMissing ? 1 : -1;
    if (leftMissing && rightMissing) return originalOrder.get(left) - originalOrder.get(right);

    const compared = type === 'number'
      ? leftNumber - rightNumber
      : collator.compare(leftValue, rightValue);
    if (compared === 0) return originalOrder.get(left) - originalOrder.get(right);
    return sortDirection === 'asc' ? compared : -compared;
  };

  const applySort = () => {
    for (const button of sortButtons) {
      const active = button.dataset.sortKey === sortKey;
      const header = button.closest('th');
      const indicator = button.querySelector('.sort-indicator');
      header.setAttribute(
        'aria-sort',
        active ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none',
      );
      indicator.textContent = active ? (sortDirection === 'asc' ? '↑' : '↓') : '↕';
    }
    if (!sortKey) return;
    const activeButton = sortButtons.find((button) => button.dataset.sortKey === sortKey);
    rows.sort((left, right) => compareRows(left, right, activeButton.dataset.sortType));
    for (const row of rows) body.append(row);
  };

  const updateScrollControls = () => {
    if (!scrollControls || !scrollLeftButton || !scrollRightButton) return;
    const maximum = Math.max(0, tableWrap.scrollWidth - tableWrap.clientWidth);
    scrollControls.hidden = maximum < 2;
    scrollLeftButton.disabled = tableWrap.scrollLeft < 2;
    scrollRightButton.disabled = tableWrap.scrollLeft > maximum - 2;
  };

  const scrollTable = (direction) => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    tableWrap.scrollBy({
      behavior: reducedMotion ? 'auto' : 'smooth',
      left: direction * Math.max(280, tableWrap.clientWidth * 0.7),
    });
  };

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
    sortKey ? url.searchParams.set('sort', sortKey) : url.searchParams.delete('sort');
    sortKey ? url.searchParams.set('direction', sortDirection) : url.searchParams.delete('direction');
    history.replaceState(null, '', url);
  };
  search.value = params.get('q') || '';
  source.value = params.get('source') || '';
  event.value = params.get('event') || '';
  search.addEventListener('input', update);
  source.addEventListener('change', update);
  event.addEventListener('change', update);
  if (scrollLeftButton && scrollRightButton) {
    scrollLeftButton.addEventListener('click', () => scrollTable(-1));
    scrollRightButton.addEventListener('click', () => scrollTable(1));
    tableWrap.addEventListener('scroll', updateScrollControls, { passive: true });
  }
  window.addEventListener('resize', updateScrollControls);
  window.addEventListener('load', updateScrollControls);
  if ('ResizeObserver' in window) new ResizeObserver(updateScrollControls).observe(tableWrap);
  for (const button of sortButtons) {
    button.addEventListener('click', () => {
      const nextKey = button.dataset.sortKey;
      sortDirection = sortKey === nextKey && sortDirection === 'asc' ? 'desc' : 'asc';
      sortKey = nextKey;
      applySort();
      update();
    });
  }
  applySort();
  update();
  updateScrollControls();
})();
