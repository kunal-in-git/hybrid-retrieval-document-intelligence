const CITATION_PATTERN = /(\[\d+\])/;

export default function AnswerText({ answer, sourceCount, onCitationClick }) {
  const parts = answer.split(CITATION_PATTERN);

  return (
    <p style={{ whiteSpace: "pre-wrap" }}>
      {parts.map((part, index) => {
        const match = part.match(/^\[(\d+)\]$/);

        if (!match) {
          return <span key={index}>{part}</span>;
        }

        const number = Number(match[1]);

        if (number < 1 || number > sourceCount) {
          return <span key={index}>{part}</span>;
        }

        return (
          <button
            key={index}
            type="button"
            onClick={() => onCitationClick(number)}
          >
            {part}
          </button>
        );
      })}
    </p>
  );
}
