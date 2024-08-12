export function setupGenreSelector(genreSelector) {
    genreSelector.addEventListener('change', function () {
      const currentGenre = genreSelector.value;
      updateGenreData(currentGenre, getCurrentViewCountType(), true);
    });
  }
  
  export function setupViewCountTypeSelector(viewCountTypeSelector) {
    viewCountTypeSelector.addEventListener('change', function () {
      const viewCountType = viewCountTypeSelector.value;
      sortTable(getCurrentColumn(), getCurrentOrder(), viewCountType);
    });
  }
  
  export function getCurrentViewCountType() {
    return document.getElementById('view-count-type-selector').value || 'total-view-count';
  }
  
  export function getCurrentColumn() {
    return document.querySelector('.sort-button[data-order]').getAttribute('data-column') || 'rank';
  }
  
  export function getCurrentOrder() {
    return document.querySelector('.sort-button[data-order]').getAttribute('data-order') || 'asc';
  }
  
  export function setCurrentColumn(column) {
    document.querySelector('.sort-button[data-column]').setAttribute('data-column', column);
  }
  
  export function setCurrentOrder(order) {
    document.querySelector('.sort-button[data-order]').setAttribute('data-order', order);
  }
  