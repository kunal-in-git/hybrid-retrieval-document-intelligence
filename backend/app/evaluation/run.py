from ..db import SessionLocal

from .runner import evaluate


def main():

    db = SessionLocal()

    try:

        evaluation = evaluate(db)

        aggregate = evaluation[
            "aggregate"
        ]

        per_query = evaluation[
            "per_query"
        ]

        # ========================================
        # Aggregate Results
        # ========================================

        print()
        print("=" * 75)
        print("HYBRID RETRIEVAL EVALUATION")
        print("=" * 75)

        print(
            f"{'Stage':<20}"
            f"{'Recall@5':<15}"
            f"{'MRR':<15}"
        )

        print("-" * 75)

        for stage, values in aggregate.items():

            print(
                f"{stage:<20}"
                f"{values['recall@5']:<15.3f}"
                f"{values['mrr']:<15.3f}"
            )

        print("=" * 75)

        # ========================================
        # Per Query Results
        # ========================================

        print()
        print("=" * 75)
        print("PER-QUERY RESULTS")
        print("=" * 75)

        for item in per_query:

            print()
            print(
                f"Query: {item['query']}"
            )

            for stage in item["stages"]:

                values = item[
                    "stages"
                ][stage]

                print(
                    f"  {stage:<18}"
                    f"Recall@5={values['recall@5']:.3f} "
                    f"MRR={values['mrr']:.3f}"
                )

        print()
        print("=" * 75)

    finally:
        db.close()


if __name__ == "__main__":
    main()