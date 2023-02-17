import plotly.io as pio

hakai_template = pio.templates["simple_white"]
hakai_axies = {"mirror": True, "ticks": "inside", "title": {"standoff": 2}}
hakai_template["layout"]["yaxis"].update(hakai_axies)
hakai_template["layout"]["xaxis"].update(hakai_axies)
hakai_template["layout"]["title"] = {
    "y": 0.95,
    "x": 0.1,
    "xanchor": "left",
    "yanchor": "top",
    "font": dict(family="Verdana", size=14, color="#000000"),
    "pad": dict(b=0, t=0, r=0, l=0),
}
hakai_template["layout"]["coloraxis"]["colorbar"] = {
    "orientation": "h",
    "thickness": 10,
    "x": 0.99,
    "y": 1.03,
    "xanchor": "right",
    "yanchor": "bottom",
    "len": 0.45,
    "xpad": 0,
    "ypad": 0.01,
}

hakai_template["layout"]["legend"] = {
    "yanchor": "bottom",
    "y": 1.02,
    "xanchor": "left",
    "x": -0.03,
    "orientation": "h",
}
hakai_template["layout"]["margin"] = dict(b=40, t=10, r=10, l=70)
