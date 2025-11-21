export function truncateTextForLines(
  text: string,
  maxLines: number,
  element: HTMLElement,
  reserveSpace: number = 30
): string {
  const computedStyle = getComputedStyle(element);
  const lineHeight = parseFloat(computedStyle.lineHeight);
  const maxHeight = lineHeight * maxLines;

  const testElement = document.createElement("div");
  testElement.style.position = "absolute";
  testElement.style.visibility = "hidden";
  testElement.style.width = `${element.offsetWidth - reserveSpace}px`;
  testElement.style.font = computedStyle.font;
  testElement.style.fontSize = computedStyle.fontSize;
  testElement.style.fontFamily = computedStyle.fontFamily;
  testElement.style.fontWeight = computedStyle.fontWeight;
  testElement.style.lineHeight = computedStyle.lineHeight;
  testElement.style.whiteSpace = "normal";
  testElement.style.wordWrap = "break-word";

  element.parentElement?.appendChild(testElement);

  const words = text.split(" ");
  let truncated = "";

  for (let i = 0; i < words.length; i++) {
    const testText = truncated + (truncated ? " " : "") + words[i];
    testElement.textContent = testText;

    const currentHeight = testElement.scrollHeight;
    const tolerance = 1;
    const exceedsMaxHeight = currentHeight > maxHeight + tolerance;

    if (exceedsMaxHeight) {
      break;
    }

    truncated = testText;
  }

  element.parentElement?.removeChild(testElement);

  return truncated;
}
