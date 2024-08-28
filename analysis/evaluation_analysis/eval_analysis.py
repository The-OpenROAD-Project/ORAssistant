import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

st.set_page_config(layout="wide")

def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

def display_metric_formulas():
    st.subheader("Metric Formulas")

    st.latex(r'''
    \text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}
    ''')

    st.latex(r'''
    \text{Precision} = \frac{TP}{TP + FP}
    ''')

    st.latex(r'''
    \text{Recall} = \frac{TP}{TP + FN}
    ''')

    st.latex(r'''
    \text{F1 Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}
    ''')

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

# In your main() function, add this line where you want to display the formulas and explanations:
display_metric_formulas()

def calculate_accuracy_counts(df):
    if 'retriever_type' in df.columns and 'acc_value' in df.columns:
        if df['acc_value'].dtype == 'object':
            df['acc_value'] = df['acc_value'].astype(str).str.strip().str.upper()
        else:
            pass

        # Exclude 'ensemble' from the groupby operation
        accuracy_counts = df[df['retriever_type'] != 'ensemble'].groupby(['retriever_type', 'acc_value']).size().unstack(fill_value=0)

        for col in ['TP', 'TN', 'FP', 'FN']:
            if col not in accuracy_counts.columns:
                accuracy_counts[col] = 0

        accuracy_counts['Total'] = accuracy_counts.sum(axis=1)

        return accuracy_counts
    else:
        st.error("Required columns 'retriever_type' or 'acc_value' not found in the DataFrame.")
        return None

def calculate_metrics(df):
    # Exclude 'ensemble' from calculations
    df_filtered = df[df['retriever_type'] != 'ensemble']

    # Calculate metrics for each retriever
    metrics = {}
    for retriever in df_filtered['retriever_type'].unique():
        retriever_data = df_filtered[df_filtered['retriever_type'] == retriever]
        
        tp = sum(retriever_data['acc_value'] == 'TP')
        tn = sum(retriever_data['acc_value'] == 'TN')
        fp = sum(retriever_data['acc_value'] == 'FP')
        fn = sum(retriever_data['acc_value'] == 'FN')
        
        total = tp + tn + fp + fn
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        llm_score = retriever_data['llm_score'].mean()
        response_time = retriever_data['response_time'].mean()

        metrics[retriever] = {
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1 Score': f1_score,
            'LLM Score': llm_score,
            'Response Time': response_time,
            'TP': tp,
            'TN': tn,
            'FP': fp,
            'FN': fn,
            'Total': total
        }

    return metrics

def main():
    st.title("Retriever Metrics Visualization")

    # Get list of CSV files in the root directory
    csv_files = [f for f in os.listdir() if f.endswith('.csv')]

    if not csv_files:
        st.error("No CSV files found in the root directory.")
        return

    # File selection dropdown with a unique key
    selected_file = st.selectbox("Select a CSV file", csv_files, key="file_selector")
    
    # Load the selected CSV file
    df = load_data(selected_file)

    # Display the selected CSV file in table format
    st.subheader(f"Contents of {selected_file}")
    st.dataframe(df)

    # Calculate metrics
    metrics = calculate_metrics(df)

    # Display accuracy counts
    st.subheader("Accuracy Value Counts per Retriever Type")
    accuracy_counts = pd.DataFrame({retriever: {'TP': m['TP'], 'TN': m['TN'], 'FP': m['FP'], 'FN': m['FN'], 'Total': m['Total']} 
                                    for retriever, m in metrics.items()}).T
    st.dataframe(accuracy_counts)

    # Visualize the distribution
    fig_acc = px.bar(accuracy_counts,
                     labels={'value': 'Count', 'variable': 'Accuracy Value'},
                     title='Distribution of Accuracy Values Across Retriever Types')
    fig_acc.update_layout(barmode='group')
    st.plotly_chart(fig_acc)

    # Define custom colors for each retriever
    custom_colors = {
        "agent-retriever": "#FFF700",  # Yellow
        "agent-retriever-sim": "#A020F0",  # Purple
        "hybrid": "#FFC0CB",  # Pink
        "sim": "#90EE90",  # Light Green
        "agent-retriever-reranker": "#FF4500"  # OrangeRed
    }

    # Update metric names to include LLM Score and Response Time
    metric_names = ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'LLM Score', 'Response Time']

    # Metric selection dropdown with a unique key
    selected_metric = st.selectbox("Select a metric to visualize", metric_names, key="metric_selector")

    # Create bar plot for the selected metric
    sorted_retrievers = sorted(metrics.keys(), key=lambda x: metrics[x][selected_metric], reverse=True if selected_metric != 'Response Time' else False)
    fig = px.bar(
        x=sorted_retrievers,
        y=[metrics[retriever][selected_metric] for retriever in sorted_retrievers],
        labels={'x': 'Retriever', 'y': selected_metric},
        title=f'{selected_metric} Comparison Across Retrievers',
        color=sorted_retrievers,
        color_discrete_map=custom_colors
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_range=[0.7, 0.8] if selected_metric == 'LLM Score' else [0.8, 1] if selected_metric != 'Response Time' else [0, max([metrics[retriever][selected_metric] for retriever in metrics]) * 1.1],
        yaxis_tickformat='.5f' if selected_metric == 'LLM Score' else '.1%' if selected_metric != 'Response Time' else '',
        height=600,
        width=800,
        legend_title="Retrievers",
        showlegend=True
    )
    fig.update_traces(
        texttemplate='%{y:.5f}' if selected_metric == 'LLM Score' else '%{y:.1%}' if selected_metric != 'Response Time' else '%{y:.2f}',
        textposition='outside'
    )
    st.plotly_chart(fig)

    # Create precision-recall graph
    fig_pr = go.Figure()

    for retriever, metric in metrics.items():
        fig_pr.add_trace(go.Scatter(
            x=[metric['Recall']],
            y=[metric['Precision']],
            mode='markers+text',
            name=retriever,
            marker=dict(size=15, color=custom_colors.get(retriever, '#000000')),  # Default to black if color not found
            text=[retriever],
            textposition="top center"
        ))

    fig_pr.update_layout(
        title='Precision vs Recall for All Retrievers',
        xaxis_title='Recall',
        yaxis_title='Precision',
        xaxis=dict(range=[0.9, 1], tickformat='.1%'),
        yaxis=dict(range=[0.9, 1], tickformat='.1%'),
        height=600,
        width=800,
        showlegend=True,
        legend_title="Retrievers"
    )
    st.plotly_chart(fig_pr)

    # Create heatmap
    heatmap_metrics = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
    heatmap_data = []
    for retriever in metrics:
        for metric in heatmap_metrics:
            heatmap_data.append([retriever, metric, metrics[retriever][metric]])

    heatmap_df = pd.DataFrame(heatmap_data, columns=['Retriever', 'Metric', 'Value'])
    heatmap_pivot = heatmap_df.pivot(index='Retriever', columns='Metric', values='Value')

    # Ensure the order of columns matches the order in heatmap_metrics
    heatmap_pivot = heatmap_pivot[heatmap_metrics]

    overall_performance = heatmap_pivot.mean(axis=1).sort_values(ascending=False)
    sorted_retrievers = overall_performance.index.tolist()

    heatmap_pivot = heatmap_pivot.loc[sorted_retrievers]

    fig_heatmap = px.imshow(heatmap_pivot,
                    labels=dict(x="Metric", y="Retriever", color="Value"),
                    x=heatmap_metrics,
                    y=heatmap_pivot.index,
                    color_continuous_scale="RdYlGn",
                    title="Heatmap of Metrics Across Retrievers")

    fig_heatmap.update_layout(
        height=600,
        width=800,
    )

    fig_heatmap.update_traces(text=heatmap_pivot.values, texttemplate="%{text:.3f}")
    fig_heatmap.update_coloraxes(colorbar_tickformat=".3f")

    st.plotly_chart(fig_heatmap)

  

if __name__ == "__main__":
    main()