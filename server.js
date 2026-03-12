const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

// Backend route
app.post("/api/chat", async (req, res) => {
  const { message, agentType } = req.body;

  console.log("User message:", message);
  console.log("Agent type:", agentType);

  // temporary response
  res.json({
    reply: `Message received: ${message} | Agent: ${agentType}`
  });
});

app.listen(5000, () => {
  console.log("Server running on port 5000");
});