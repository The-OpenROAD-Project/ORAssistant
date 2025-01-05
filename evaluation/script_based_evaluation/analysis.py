import streamlit as st
import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore

st.set_page_config(layout="wide")


def load_data(file_path):
    df = pd.read_csv(file_path)
    return df


def display_metric_formulas():
    st.subheader("Metric Formulas")

    st.latex(r"""
    \text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}
    """)

    st.latex(r"""
    \text{Precision} = \frac{TP}{TP + FP}
    """)

    st.latex(r"""
    \text{Recall} = \frac{TP}{TP + FN}
    """)

    st.latex(r"""
    \text{F1 Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}
    """)

    st.markdown("""
    Where:
    - TP = True Positives
    - TN = True Negatives
    - FP = False Positives
    - FN = False Negatives
    """)

    st.subheader("Explanation of TP, TN, FP, FN")

    st.markdown("""
    **True Positive (TP):**
    - Description: The model provided a correct and relevant answer.
    - Example:
        - Question: "What does CTS stand for in the OpenROAD flow?"
        - Model Answer: "CTS stands for Clock Tree Synthesis. It is a stage in the OpenROAD flow that synthesizes the clock distribution network. CTS inserts clock buffers to distribute the clock signal to all sequential elements while minimizing skew. The CTS metrics reported include the number of clock roots, number of buffers inserted, number of clock subnets, and number of sinks."
        - Evaluation: TP (The model provided a detailed, accurate, and relevant answer.)

    **True Negative (TN):**
    - Description: The model correctly identified that it couldn't answer a question or that the question was out of scope.
    - Example:
        - Question: "What is the latest movie released in theaters?"
        - Model Answer: "I can't provide information on movies as it is out of my scope."
        - Evaluation: TN (The model correctly identified that the question was out of scope.)

    **False Positive (FP):**
    - Description: The model provided an answer that it thought was correct, but was actually incorrect or irrelevant.
    - Example:
        - Question: "What does CTS stand for in the OpenROAD flow?"
        - Model Answer: "CTS stands for Central Time Scheduling. It is a process used in schools to manage class schedules."
        - Evaluation: FP (The model provided an incorrect and irrelevant answer.)

    **False Negative (FN):**
    - Description: The model failed to provide an answer when it should have been able to.
    - Example:
        - Question: "What does CTS stand for in the OpenROAD flow?"
        - Model Answer: "I cannot provide an answer to this question."
        - Evaluation: FN (The model failed to provide an answer when it was expected to.)
    """)


def calculate_accuracy_counts(df):
    if "architecture" in df.columns and "acc_value" in df.columns:
        if df["acc_value"].dtype == "object":
            df["acc_value"] = df["acc_value"].astype(str).str.strip().str.upper()
        else:
            pass

        accuracy_counts = (
            df.groupby(["architecture", "acc_value"]).size().unstack(fill_value=0)
        )

        for col in ["TP", "TN", "FP", "FN"]:
            if col not in accuracy_counts.columns:
                accuracy_counts[col] = 0

        accuracy_counts["Total"] = accuracy_counts.sum(axis=1)

        return accuracy_counts
    else:
        st.error(
            "Required columns 'architecture' or 'acc_value' not found in the DataFrame."
        )
        return None


def calculate_metrics(df):
    # Calculate metrics for each architecture
    metrics = {}
    for arch in df["architecture"].unique():
        arch_data = df[df["architecture"] == arch]

        tp = sum(arch_data["acc_value"] == "TP")
        tn = sum(arch_data["acc_value"] == "TN")
        fp = sum(arch_data["acc_value"] == "FP")
        fn = sum(arch_data["acc_value"] == "FN")

        total = tp + tn + fp + fn
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        llm_score = arch_data["llm_score"].mean()
        response_time = arch_data["response_time"].mean()

        metrics[arch] = {
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1 Score": f1_score,
            "LLM Score": llm_score,
            "Response Time": response_time,
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn,
            "Total": total,
        }

    return metrics


def main():
    st.title("Architecture Metrics Visualization")

    # Get list of CSV files in the current directory
    selected_file = "data/data_result.csv"

    # Load the selected CSV file
    df = load_data(selected_file)

    # Display the selected CSV file in table format
    st.subheader(f"Contents of {selected_file}")
    st.dataframe(df)

    # Display metric formulas and explanations
    display_metric_formulas()

    # Calculate metrics
    metrics = calculate_metrics(df)

    # Display accuracy counts
    st.subheader("Accuracy Value Counts per Architecture")
    accuracy_counts = pd.DataFrame(
        {
            arch: {
                "TP": m["TP"],
                "TN": m["TN"],
                "FP": m["FP"],
                "FN": m["FN"],
                "Total": m["Total"],
            }
            for arch, m in metrics.items()
        }
    ).T
    st.dataframe(accuracy_counts)

    st.subheader("Distribution of Accuracy Values Across Architectures")
    accuracy_counts_melted = accuracy_counts.reset_index().melt(
        id_vars="index", value_vars=["TP", "TN", "FP", "FN"]
    )
    accuracy_counts_melted.columns = ["Architecture", "Accuracy Value", "Count"]
    fig_acc = px.bar(
        accuracy_counts_melted,
        x="Architecture",
        y="Count",
        color="Accuracy Value",
        barmode="group",
        title="Distribution of Accuracy Values Across Architectures",
        labels={
            "Architecture": "Architecture",
            "Count": "Count",
            "Accuracy Value": "Accuracy Value",
        },
    )
    st.plotly_chart(fig_acc)

    custom_colors = {
        "v1": "#1f77b4",  # Blue
        "v2": "#ff7f0e",  # Orange
        "base-gemini-1.5-flash": "#2ca02c",  # Green
        "base-gpt-4o": "#d62728",  # Red
    }

    metric_names = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
        "LLM Score",
        "Response Time",
    ]
    selected_metric = st.selectbox(
        "Select a metric to visualize", metric_names, key="metric_selector"
    )

    st.subheader(f"{selected_metric} Comparison Across Architectures")
    sorted_architectures = sorted(
        metrics.keys(),
        key=lambda x: metrics[x][selected_metric],
        reverse=True if selected_metric != "Response Time" else False,
    )
    fig = px.bar(
        x=sorted_architectures,
        y=[metrics[arch][selected_metric] for arch in sorted_architectures],
        labels={"x": "Architecture", "y": selected_metric},
        title=f"{selected_metric} Comparison Across Architectures",
        color=sorted_architectures,
        color_discrete_map=custom_colors,
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_range=[0.7, 1]
        if selected_metric != "Response Time"
        else [0, max([metrics[arch][selected_metric] for arch in metrics]) * 1.1],
        yaxis_tickformat=".5f"
        if selected_metric == "LLM Score"
        else ".1%"
        if selected_metric != "Response Time"
        else "",
        height=600,
        width=800,
        legend_title="Architectures",
        showlegend=False,
    )
    fig.update_traces(
        texttemplate="%{y:.5f}"
        if selected_metric == "LLM Score"
        else "%{y:.1%}"
        if selected_metric != "Response Time"
        else "%{y:.2f}",
        textposition="outside",
    )
    st.plotly_chart(fig)

    # Create precision-recall graph
    st.subheader("Precision vs Recall for All Architectures")
    fig_pr = go.Figure()

    for arch, metric in metrics.items():
        fig_pr.add_trace(
            go.Scatter(
                x=[metric["Recall"]],
                y=[metric["Precision"]],
                mode="markers+text",
                name=arch,
                marker=dict(
                    size=15, color=custom_colors.get(arch, "#000000")
                ),  # Default to black if color not found
                text=[arch],
                textposition="top center",
            )
        )

    fig_pr.update_layout(
        title="Precision vs Recall for All Architectures",
        xaxis_title="Recall",
        yaxis_title="Precision",
        xaxis=dict(range=[0.9, 1], tickformat=".1%"),
        yaxis=dict(range=[0.9, 1], tickformat=".1%"),
        height=600,
        width=800,
        showlegend=False,
    )
    st.plotly_chart(fig_pr)

    # Create heatmap
    st.subheader("Heatmap of Metrics Across Architectures")
    heatmap_metrics = ["Accuracy", "Precision", "Recall", "F1 Score"]
    heatmap_data = []
    for arch in metrics:
        for metric in heatmap_metrics:
            heatmap_data.append([arch, metric, metrics[arch][metric]])

    heatmap_df = pd.DataFrame(heatmap_data, columns=["Architecture", "Metric", "Value"])
    heatmap_pivot = heatmap_df.pivot(
        index="Architecture", columns="Metric", values="Value"
    )

    # Ensure the order of columns matches the order in heatmap_metrics
    heatmap_pivot = heatmap_pivot[heatmap_metrics]

    overall_performance = heatmap_pivot.mean(axis=1).sort_values(ascending=False)
    sorted_architectures = overall_performance.index.tolist()

    heatmap_pivot = heatmap_pivot.loc[sorted_architectures]

    fig_heatmap = px.imshow(
        heatmap_pivot,
        labels=dict(x="Metric", y="Architecture", color="Value"),
        x=heatmap_metrics,
        y=heatmap_pivot.index,
        color_continuous_scale="RdYlGn",
        title="Heatmap of Metrics Across Architectures",
    )

    fig_heatmap.update_layout(
        height=600,
        width=800,
    )

    fig_heatmap.update_traces(text=heatmap_pivot.values, texttemplate="%{text:.3f}")
    fig_heatmap.update_coloraxes(colorbar_tickformat=".3f")

    st.plotly_chart(fig_heatmap)


if __name__ == "__main__":
    main()
