import styles from "./AnswerText.module.css";

const CITATION_PATTERN = /(\[\d+\])/;

export default function AnswerText({ answer, sourceCount, onCitationClick }) {
  const parts = answer.split(CITATION_PATTERN);

  return (
    <p className={styles.answer}>
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
            className={styles.citation}
            onClick={() => onCitationClick(number)}
            title={`Show source ${number}`}
          >
            {number}
          </button>
        );
      })}
    </p>
  );
}
