#!/usr/bin/env node
/**
 * Smallest AI Lightning STT - Batch Transcription
 *
 * Transcribe audio files using the Lightning STT API.
 * Outputs both a plain text transcript and a JSON result file.
 *
 * Setup:
 *     npm install
 *
 *     export SMALLEST_API_KEY="your-api-key-here"
 *     # Get your API key at: https://smallest.ai/console
 *
 * Usage:
 *     node transcribe.js <audio_file> [--language <code>] [--output-dir <dir>]
 *
 * Examples:
 *     node transcribe.js recording.wav
 *     node transcribe.js podcast.mp3 --language en
 *     node transcribe.js meeting.wav --language multi --output-dir ./results
 */

const fs = require("fs");
const path = require("path");

const API_URL = "https://waves-api.smallest.ai/api/v1/lightning/get_text";

function getApiKey() {
  const apiKey = process.env.SMALLEST_API_KEY;
  if (!apiKey) {
    console.error("Error: SMALLEST_API_KEY environment variable not set.");
    console.error("Get your API key at: https://smallest.ai/console");
    process.exit(1);
  }
  return apiKey;
}

function parseArgs() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error("Usage: node transcribe.js <audio_file> [--language <code>] [--output-dir <dir>]");
    console.error("");
    console.error("Examples:");
    console.error("  node transcribe.js recording.wav");
    console.error("  node transcribe.js podcast.mp3 --language en");
    process.exit(1);
  }

  const result = {
    audioFile: args[0],
    language: "multi",
    outputDir: ".",
  };

  for (let i = 1; i < args.length; i++) {
    if (args[i] === "--language" || args[i] === "-l") {
      result.language = args[++i] || "multi";
    } else if (args[i] === "--output-dir" || args[i] === "-o") {
      result.outputDir = args[++i] || ".";
    }
  }

  return result;
}

async function transcribeAudio(audioPath, language = "multi") {
  const apiKey = getApiKey();

  if (!fs.existsSync(audioPath)) {
    throw new Error(`Audio file not found: ${audioPath}`);
  }

  const audioData = fs.readFileSync(audioPath);
  const url = `${API_URL}?language=${encodeURIComponent(language)}`;

  console.log(`Transcribing: ${path.basename(audioPath)}`);
  console.log(`Language: ${language.toLowerCase() === "multi" ? "auto-detect (multi)" : language}`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/octet-stream",
    },
    body: audioData,
  });

  if (!response.ok) {
    let errorMsg = `API request failed with status ${response.status}`;
    try {
      const errorDetail = await response.json();
      errorMsg += `: ${JSON.stringify(errorDetail)}`;
    } catch {
      errorMsg += `: ${await response.text()}`;
    }
    throw new Error(errorMsg);
  }

  return await response.json();
}

function saveResults(result, outputDir = ".") {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const transcriptPath = path.join(outputDir, "transcript.txt");
  fs.writeFileSync(transcriptPath, result.transcription || "", "utf-8");
  console.log(`Saved transcript: ${transcriptPath}`);

  const jsonPath = path.join(outputDir, "result.json");
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), "utf-8");
  console.log(`Saved result: ${jsonPath}`);

  return { transcriptPath, jsonPath };
}

async function main() {
  const args = parseArgs();

  try {
    const result = await transcribeAudio(args.audioFile, args.language);

    if (result.status !== "success") {
      console.error(`Transcription failed: ${JSON.stringify(result)}`);
      process.exit(1);
    }

    console.log("");
    console.log("=".repeat(60));
    console.log("TRANSCRIPTION");
    console.log("=".repeat(60));
    console.log(result.transcription || "");
    console.log("=".repeat(60));
    console.log("");

    saveResults(result, args.outputDir);

    console.log("\nDone!");
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

main();

