import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import 'tdesign-vue-next/dist/tdesign.css'
import {
  Button,
  Layout,
  Aside,
  Header,
  Content,
  Footer,
  Menu,
  MenuItem,
  Submenu,
  Card,
  Tree,
  TreeSelect,
  Breadcrumb,
  BreadcrumbItem,
  Dropdown,
  DropdownMenu,
  DropdownItem,
  Form,
  FormItem,
  Input,
  InputNumber,
  Textarea,
  Table,
  Tag,
  Link,
  Space,
  Pagination,
  Dialog,
  DialogPlugin,
  Message,
  MessagePlugin,
  Loading,
  LoadingPlugin,
  ConfigProvider,
  Icon,
  Checkbox,
  Select,
  Option,
  Row,
  Col,
  Popup,
  Tooltip,
  List,
  ListItem,
  ListItemMeta,
  Empty,
  Upload,
  Progress,
  Tabs,
  TabPanel,
  Slider,
  Drawer,
  Radio,
  RadioGroup,
  RadioButton,
  Divider,
  Alert,
  Descriptions,
  DescriptionsItem
} from 'tdesign-vue-next'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Layout)
app.use(Aside)
app.use(Header)
app.use(Content)
app.use(Footer)
app.use(Button)
app.use(Menu)
app.use(MenuItem)
app.use(Submenu)
app.use(Card)
app.use(Tree)
app.use(Breadcrumb)
app.use(BreadcrumbItem)
app.use(Dropdown)
app.use(DropdownMenu)
app.use(DropdownItem)
app.use(Form)
app.use(FormItem)
app.use(Input)
app.use(InputNumber)
app.use(Textarea)
app.use(Table)
app.use(Tag)
app.use(Link)
app.use(Space)
app.use(Pagination)
app.use(Dialog)
app.use(Loading)
app.use(ConfigProvider)
app.use(Icon)
app.use(Checkbox)
app.use(Select)
app.use(Option)
app.use(Row)
app.use(Col)
app.use(Popup)
app.use(Tooltip)
app.use(List)
app.use(ListItem)
app.use(ListItemMeta)
app.use(Empty)
app.use(Upload)
app.use(Progress)
app.use(Tabs)
app.use(TabPanel)
app.use(Slider)
app.use(TreeSelect)
app.use(Drawer)
app.use(Radio)
app.use(RadioGroup)
app.use(RadioButton)
app.use(Divider)
app.use(Alert)
app.use(Descriptions)
app.use(DescriptionsItem)

app.config.globalProperties.$message = Message
app.config.globalProperties.$loading = Loading
app.config.globalProperties.$dialog = DialogPlugin
app.config.globalProperties.$notify = MessagePlugin

app.mount('#app')