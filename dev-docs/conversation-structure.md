# Conversation structure


## Structure

The conversation as returned by `Messages.prompt()` consists of a list of messages, where each message is a dictionary with role and content keys.

[
	{
		"role": 	"system",
		"content":	"System prompt"
	},
	{
		"role": 	"user"|"assistant"|tool",
		"content":	"Message content"
	},
	...
]

The role is always "system" for the first message, and "user", "assistant", or "tool" for the rest. There are always at least two messages. No particular order of message roles is enforced.


## Context

Context that usually doesn't change over the conversation, such as foundation documents, are included in the system prompt so that they can be cached if the AI provider supports it. Context that changes often, such as incidental documents, are included in a context section in the last user message (if present), so that they don't interfere with caching.


## Thinking blocks

If the AI returns thinking blocks, these are embedded as HTML elements in assistant messages.


## Workspace

The workspace is set when included in a user message.


## Tool calls and results

A tool always consists of an assistant message followed by a tool message. The tool message contains a JSON dump of the tool result. If the tool requires feedback, then this is followed by another assistant message that allows the assistant to process the tool result.

[
	...,
	{
		"role": 	"assistant",
		"content":	"Message that accompanied the tool call"
	},
	{
		"role": 	"tool",
		"content":	"(see below)"
	},
	{
		"role": 	"assistant",
		"content":	"Message in response to tool result. Only present for tools that require feedback."
	},	
	...
]

Tool results should have the following structure. This should be serialized to a string and uses as the content of the tool message.

{
	"name": "tool_name",
	"args": {
		"arg1": "val1"
	},
	"content": "tool result"
}
