import copy
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing_extensions import Self
from typing import List, Optional, Any, Dict, Union

from dataclasses_json import dataclass_json, config, DataClassJsonMixin


class FinishReason(Enum):
    stop = "stop"
    length = "length"


@dataclass_json
@dataclass
class MessageText(DataClassJsonMixin):
    content: str


class RoleValue(Enum):
    Assistant = "assistant"
    User = "user"
    # ASSISTANT = "assistant"
    # USER = "user"


@dataclass_json
@dataclass
class Role(DataClassJsonMixin):
    role: RoleValue = field(metadata=config(encoder=lambda x: x.value, decoder=RoleValue))


@dataclass_json
@dataclass
class MessageData(DataClassJsonMixin):
    index: int
    delta: Union[MessageText, Role]
    finish_reason: Optional[FinishReason] = field(metadata=config(encoder=lambda x: x.value, decoder=FinishReason))


@dataclass_json
@dataclass
class OfflineMessageData:
    index: int
    role: Role
    message: MessageText

    @classmethod
    def create_from_choices(cls, choices: List[MessageData]) -> Optional[Self]:
        # we manage only the first occurrence, never seen a list with more than one value...
        try:
            ch = choices[0]
            delta = ch.delta
            if isinstance(delta, MessageText):
                return cls(index=ch.index, role=None, message=delta)
            elif isinstance(delta, Role):
                return cls(index=ch.index, role=delta, message=None)
            elif isinstance(delta, Dict):
                role = delta.get('role')
                if role and role.lower() == 'assistant':
                    return cls(index=ch.index, role=Role(role=RoleValue.Assistant), message=None)
                elif role and role.lower() == 'user':
                    return cls(index=ch.index, role=Role(role=RoleValue.User), message=None)
                msg = delta.get('content')
                if msg:
                    return cls(index=ch.index, role=None, message=MessageText(content=msg))

                raise ValueError(f"I do not manage delta of type: {delta}")
            else:
                raise ValueError(f"I do not manage delta of type: {delta}")
        except Exception as e:
            print(f"ERROR while creating OfflineMessageData from {choices=} with error {e}")
            return None


def encode_message_list(messages: List[MessageData]) -> str:
    l = [MessageData.schema().dump(y) for y in messages]
    ret = "["
    ret += ",".join(l)
    ret += "]"
    return ret


def decode_message_list(messages: List[MessageData]) -> List[MessageData]:
    for message in messages:
        js: Dict = message.delta
        if js.get('role'):
            message.delta = Role.schema().load(js)
        elif js.get('content'):
            message.delta = MessageText.schema().load(js)
        else:
            raise ValueError(f"Unexected value {js=}")
    return messages


@dataclass_json
@dataclass
class Message:
    id: str
    model: str
    created: int
    object: str
    choices: List[MessageData] = field(metadata=config(
        encoder=encode_message_list,
        decoder=decode_message_list))


@dataclass_json
@dataclass
class OfflineMessage:
    id: str
    model: str
    created: int
    object: str
    message: OfflineMessageData

    @classmethod
    def create_from_message(cls, message: Message) -> Optional[Self]:
        choices = OfflineMessageData.create_from_choices(message.choices)
        if choices:
            return cls(id=message.id, model=message.model, created=message.created, object=message.object,
                       message=choices)
        else:
            return None


@dataclass_json
@dataclass
class QA(DataClassJsonMixin):
    parent_id: Optional[str]
    user_message: OfflineMessage
    assistant_message: OfflineMessage


def create_message(json: Any) -> Message:
    return Message.schema().load(json)


def pack_and_save_message(storage: Path, previous_uuid: Optional[str], messages: List[Dict[str, str] | Message]):
    assistant_message: Optional[OfflineMessage] = None
    user_message = None
    for m in messages:
        if isinstance(m, Message):
            if assistant_message is None:
                assistant_message = OfflineMessage.create_from_message(m)
                if assistant_message.message.role is None:
                    assistant_message.message.role = RoleValue.Assistant
                if assistant_message.message.message is None:
                    assistant_message.message.message = MessageText(content="")
            else:
                if isinstance(m.choices[0].delta, MessageText):
                    assistant_message.message.message.content += m.choices[0].delta.content
        else:
            # this is the question from the user.
            user_message = m

    if user_message and assistant_message:
        message = user_message.get("content")
        user_message = copy.deepcopy(assistant_message)
        user_message.message.role = RoleValue.User
        user_message.message.message.content = message

        id = user_message.id
        qa = QA(previous_uuid, user_message, assistant_message)
        with (storage / f"{id}.json").open("w") as fi:
            fi.write(qa.to_json(indent=2))


if __name__ == '__main__':
    role = Role(role=RoleValue.Assistant)
    print(f"{role.role.value=}")
    print(role.to_json())
    print(Role(role=RoleValue.User).to_json())
    try:
        role_value = Role.schema().load({
            "role": "assistant"
        })
    except Exception as e:
        print(f"Error: {e}")
        exit(2)
    print(f"{role_value=}")

    a = create_message({
        "id": "truc-machin-123",
        "model": "gpt-123345",
        "created": 12345678,
        "object": "do not remember its value",
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant"
                },
                "finish_reason": "stop",
            }
        ]
    })

    print(a)
