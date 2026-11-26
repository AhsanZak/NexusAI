import type { ReactNode } from "react";

type Block = { kind: "paragraph"; text: string } | { kind: "list"; items: string[] };

export function AnswerText({ text }: { text: string }) {
  const blocks = blocksFrom(text);
  return (
    <div className="answer-text" style={{ lineHeight: 1.65 }}>
      {blocks.map((block, index) =>
        block.kind === "list" ? (
          <ul key={index} style={{ margin: "4px 0 12px", paddingInlineStart: 22 }}>
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex} style={{ marginBottom: 6 }}>
                {inline(item)}
              </li>
            ))}
          </ul>
        ) : (
          <p key={index} style={{ margin: "0 0 10px" }}>
            {inline(block.text)}
          </p>
        ),
      )}
    </div>
  );
}

function blocksFrom(text: string): Block[] {
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let items: string[] = [];

  const flushParagraph = () => {
    const joined = paragraph.join(" ").trim();
    paragraph = [];
    if (joined) {
      blocks.push({ kind: "paragraph", text: joined });
    }
  };
  const flushList = () => {
    if (items.length > 0) {
      blocks.push({ kind: "list", items });
      items = [];
    }
  };

  for (const line of text.replace(/\r\n/g, "\n").split("\n")) {
    const bullet = /^\s*(?:[-*]|\d+[.)])\s+(.*)$/.exec(line);
    if (bullet) {
      flushParagraph();
      items.push(bullet[1]);
      continue;
    }
    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }
    flushList();
    paragraph.push(line.trim());
  }
  flushParagraph();
  flushList();
  return blocks;
}

function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+?\*\*)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}
