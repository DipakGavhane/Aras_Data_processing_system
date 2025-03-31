from flask import Flask, render_template_string
import plotly
import plotly.graph_objs as go
import json

app = Flask(__name__)


@app.route('/')
def index():
    # Sample student data: each student has a roll number, name, and sgpa
    data = [
        {"roll": "101", "name": "Alice", "sgpa": 8.5},
        {"roll": "102", "name": "Bob", "sgpa": 7.8},
        {"roll": "103", "name": "Charlie", "sgpa": 9.2},
        {"roll": "104", "name": "David", "sgpa": 8.1},
        {"roll": "105", "name": "Eve", "sgpa": 9.0},
        {"roll": "106", "name": "Frank", "sgpa": 7.5}
    ]

    # Sort data by roll number for consistent x-axis order
    data_sorted = sorted(data, key=lambda x: x["roll"])
    x_values = [d["roll"] for d in data_sorted]
    y_values = [d["sgpa"] for d in data_sorted]

    # Create a line trace for all students
    line_trace = go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name='All Students',
        line=dict(color='blue')
    )

    # Determine top 3 students by sgpa (highest values)
    top_students = sorted(data, key=lambda x: x["sgpa"], reverse=True)[:3]

    # Create a trace for each top student to highlight them
    top_traces = []
    for student in top_students:
        top_trace = go.Scatter(
            x=[student["roll"]],
            y=[student["sgpa"]],
            mode='markers',
            name=student["name"],
            marker=dict(
                size=12,
                color='red'
            )
        )
        top_traces.append(top_trace)

    # Define layout with the y-axis fixed to the range 4-10
    layout = go.Layout(
        title='Students SGPA Data',
        xaxis=dict(title='Roll Number'),
        yaxis=dict(title='SGPA', range=[4, 10])
    )

    # Combine the traces: the overall line and the top student markers
    fig = go.Figure(data=[line_trace] + top_traces, layout=layout)

    # Convert the figure to JSON for rendering with Plotly.js
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Render the chart in an HTML template
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Student SGPA Line Chart</title>

    </head>
    <body>
        
        <script>
            var fig = {{ graphJSON | safe }};
            Plotly.newPlot('chart', fig.data, fig.layout, { displayModeBar: false });
        </script>
    </body>
    </html>
    ''', graphJSON=graphJSON)


if __name__ == '__main__':
    app.run(debug=True)
