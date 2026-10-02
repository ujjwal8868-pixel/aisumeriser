import React, { useState } from "react";

function App() {
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [file, setFile] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [mode, setMode] = useState("text");
  const [loading, setLoading] = useState(false);

  const summarizeText = async () => {
    if (!text.trim()) {
      alert("Please enter some text.");
      return;
    }

    setLoading(true);
    setSummary("");

    try {
      const response = await fetch("http://127.0.0.1:5000/summarise/text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text,
        }),
      });

      const data = await response.json();
      setSummary(data.summary || data.error || "No summary available.");
    } catch (error) {
      console.error(error);
      setSummary("Unable to connect to the backend.");
    }

    setLoading(false);
  };

  const summarizePDF = async () => {
    if (!file) {
      alert("Please select a PDF file.");
      return;
    }

    setLoading(true);
    setSummary("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/summarize/pdf",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();
      setSummary(data.summary || data.error || "No summary available.");
    } catch (error) {
      console.error(error);
      setSummary("Unable to connect to the backend.");
    }

    setLoading(false);
  };

  const summarizeYouTube = async () => {
    if (!youtubeUrl.trim()) {
      alert("Please enter a YouTube URL.");
      return;
    }

    setLoading(true);
    setSummary("");

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/summarize/youtube",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            url: youtubeUrl,
          }),
        }
      );

      const data = await response.json();
      setSummary(data.summary || data.error || "No summary available.");
    } catch (error) {
      console.error(error);
      setSummary("Unable to connect to the backend.");
    }

    setLoading(false);
  };

  const handleSummarize = () => {
    if (mode === "text") {
      summarizeText();
    } else if (mode === "pdf") {
      summarizePDF();
    } else {
      summarizeYouTube();
    }
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>AI Summarizer</h1>

      <p>Summarize Text, PDF and YouTube videos using AI.</p>

      <div style={{ marginBottom: "20px" }}>
        <button onClick={() => setMode("text")}>Text</button>
        <button onClick={() => setMode("pdf")}>PDF</button>
        <button onClick={() => setMode("youtube")}>YouTube</button>
      </div>

      {mode === "text" && (
        <textarea
          rows="10"
          cols="70"
          placeholder="Enter your text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      )}

      {mode === "pdf" && (
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files[0])}
        />
      )}

      {mode === "youtube" && (
        <input
          type="text"
          placeholder="Enter YouTube URL"
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          style={{ width: "400px", padding: "10px" }}
        />
      )}

      <br />
      <br />

      <button onClick={handleSummarize} disabled={loading}>
        {loading ? "Summarizing..." : "Summarize"}
      </button>

      {summary && (
        <div style={{ marginTop: "30px" }}>
          <h2>Summary</h2>
          <p>{summary}</p>
        </div>
      )}
    </div>
  );
}

export default App;